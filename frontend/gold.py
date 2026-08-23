"""Acesso somente leitura às views atuais da camada Gold."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import streamlit as st

QUERY_TTL_SECONDS = 300

CURRENT_VIEWS = frozenset(
    {
        "gold.vw_market_overview_current",
        "gold.vw_project_investment_current",
        "gold.vw_project_location_current",
        "gold.vw_status_distribution_current",
        "gold.vw_snapshot_metadata_current",
        "gold.vw_project_detail_current",
        "gold.vw_project_participant_current",
        "gold.vw_project_axis_type_current",
        "gold.vw_project_ppa_current",
        "gold.vw_project_restriction_area_current",
        "gold.vw_project_photo_indicator_current",
        "gold.vw_project_contract_current",
        "gold.vw_project_commitment_current",
        "gold.vw_project_commitment_totals_current",
        "gold.vw_project_execution_current",
        "gold.vw_project_status_history_current",
        "gold.vw_project_feasibility_study_current",
        "gold.vw_project_coverage_current",
    }
)

MARKET_OVERVIEW_COLUMNS = (
    "project_id",
    "project_name",
    "description",
    "organization_name",
    "organization_cnpj",
    "source_status",
    "uf_principal",
    "nature_intervention",
    "species_intervention",
    "axis_name",
    "type_name",
    "subtype_name",
    "registration_date",
    "registration_year",
    "expected_start_date",
    "expected_end_date",
    "planned_investment_amount",
    "municipality_names",
    "ibge_codes",
    "source_updated_at",
    "ingested_at",
    "ingestion_id",
)

PROJECT_INVESTMENT_COLUMNS = (
    "project_id",
    "funding_source_name",
    "planned_investment_amount",
    "source_updated_at",
    "ingested_at",
    "ingestion_id",
)

PROJECT_LOCATION_COLUMNS = (
    "project_id",
    "municipality_name",
    "ibge_code",
    "uf",
    "geometry_origin",
    "latitude",
    "longitude",
    "planned_investment_amount",
)

STATUS_DISTRIBUTION_COLUMNS = ("source_status", "project_count")
FILTERED_KPI_COLUMNS = (
    "project_count",
    "planned_investment_amount",
    "municipality_count",
    "execution_project_count",
)
SNAPSHOT_METADATA_COLUMNS = (
    "ingestion_id",
    "source_updated_at",
    "ingested_at",
    "project_count",
    "planned_investment_amount",
    "municipality_count",
    "execution_project_count",
)

_VIEW_QUERIES: dict[str, tuple[str, tuple[str, ...]]] = {
    "gold.vw_market_overview_current": (
        """
        SELECT
            project_id,
            project_name,
            description,
            organization_name,
            organization_cnpj,
            source_status,
            uf_principal,
            nature_intervention,
            species_intervention,
            axis_name,
            type_name,
            subtype_name,
            registration_date,
            registration_year,
            expected_start_date,
            expected_end_date,
            planned_investment_amount,
            municipality_names,
            ibge_codes,
            source_updated_at,
            ingested_at,
            ingestion_id
        FROM gold.vw_market_overview_current
        ORDER BY project_name NULLS LAST, project_id
        """,
        MARKET_OVERVIEW_COLUMNS,
    ),
    "gold.vw_project_investment_current": (
        """
        SELECT
            project_id,
            funding_source_name,
            planned_investment_amount,
            source_updated_at,
            ingested_at,
            ingestion_id
        FROM gold.vw_project_investment_current
        ORDER BY project_id, funding_source_name NULLS LAST
        """,
        PROJECT_INVESTMENT_COLUMNS,
    ),
    "gold.vw_project_location_current": (
        """
        SELECT
            project_id,
            municipality_name,
            ibge_code,
            uf,
            geometry_origin,
            latitude,
            longitude,
            planned_investment_amount
        FROM gold.vw_project_location_current
        ORDER BY municipality_name NULLS LAST, project_id
        """,
        PROJECT_LOCATION_COLUMNS,
    ),
    "gold.vw_status_distribution_current": (
        """
        SELECT source_status, project_count
        FROM gold.vw_status_distribution_current
        ORDER BY project_count DESC NULLS LAST, source_status NULLS LAST
        """,
        STATUS_DISTRIBUTION_COLUMNS,
    ),
    "gold.vw_snapshot_metadata_current": (
        """
        SELECT
            ingestion_id,
            source_updated_at,
            ingested_at,
            project_count,
            planned_investment_amount,
            municipality_count,
            execution_project_count
        FROM gold.vw_snapshot_metadata_current
        ORDER BY ingested_at DESC NULLS LAST
        LIMIT 1
        """,
        SNAPSHOT_METADATA_COLUMNS,
    ),
}

_FILTERED_KPI_QUERY = """
WITH filtered_projects AS (
    SELECT
        project_id,
        planned_investment_amount,
        source_status
    FROM gold.vw_market_overview_current
    WHERE project_id = ANY(CAST(:project_ids AS text[]))
),
filtered_locations AS (
    SELECT location.project_id, location.ibge_code
    FROM gold.vw_project_location_current AS location
    INNER JOIN filtered_projects AS project
        ON project.project_id = location.project_id
    WHERE :has_municipality_filter = false
       OR location.municipality_name = ANY(CAST(:municipalities AS text[]))
),
project_metrics AS (
    SELECT
        count(*)::bigint AS project_count,
        sum(planned_investment_amount)::numeric AS planned_investment_amount,
        count(*) FILTER (WHERE source_status = 'Em execução')::bigint
            AS execution_project_count
    FROM filtered_projects
),
location_metrics AS (
    SELECT count(DISTINCT ibge_code)::bigint AS municipality_count
    FROM filtered_locations
)
SELECT
    project_metrics.project_count,
    project_metrics.planned_investment_amount,
    location_metrics.municipality_count,
    project_metrics.execution_project_count
FROM project_metrics
CROSS JOIN location_metrics
"""

_FILTERED_STATUS_QUERY = """
SELECT
    source_status::text AS source_status,
    count(*)::bigint AS project_count
FROM gold.vw_market_overview_current
WHERE project_id = ANY(CAST(:project_ids AS text[]))
GROUP BY source_status
ORDER BY project_count DESC NULLS LAST, source_status NULLS LAST
"""

DETAIL_VIEW_COLUMNS: dict[str, tuple[str, ...]] = {
    "gold.vw_project_detail_current": (
        "project_id", "project_name", "description", "organization_name", "organization_cnpj",
        "source_status", "uf_principal", "nature_intervention", "species_intervention",
        "registration_date", "registration_year", "expected_start_date", "expected_end_date",
        "actual_start_date", "actual_end_date", "structural_project_indicator", "postal_code",
        "address_description", "social_function_description", "global_goal_description",
        "benefited_population", "benefited_population_description", "jobs_created_count",
        "bim_indicator", "intervention_notes", "source_system", "feasibility_study_indicator",
        "planned_investment_amount",
        "source_updated_at", "ingested_at", "ingestion_id",
    ),
    "gold.vw_project_participant_current": (
        "project_id", "participant_role", "organization_key", "organization_name",
        "organization_cnpj", "source_participant_count", "source_updated_at", "ingested_at",
        "ingestion_id",
    ),
    "gold.vw_project_location_current": (
        "project_id", "municipality_name", "ibge_code", "uf", "geometry_id", "geometry_origin",
        "latitude", "longitude", "pin_name", "source_updated_at", "ingested_at", "ingestion_id",
    ),
    "gold.vw_project_investment_current": PROJECT_INVESTMENT_COLUMNS,
    "gold.vw_project_axis_type_current": (
        "project_id", "axis_id", "axis_name", "type_id", "type_name", "subtype_id",
        "subtype_name", "source_updated_at", "ingested_at", "ingestion_id",
    ),
    "gold.vw_project_ppa_current": (
        "project_id", "ppa_type", "ppa_description", "source_updated_at", "ingested_at",
        "ingestion_id",
    ),
    "gold.vw_project_restriction_area_current": (
        "project_id", "restriction_area", "source_updated_at", "ingested_at", "ingestion_id",
    ),
    "gold.vw_project_photo_indicator_current": (
        "project_id", "ind_foto", "source_updated_at", "ingested_at", "ingestion_id",
    ),
    "gold.vw_project_contract_current": (
        "project_id", "contract_source_id", "contract_number", "supplier_name", "supplier_cnpj",
        "contract_status", "validity_start_date", "validity_end_date", "contract_object",
        "process_number", "modality", "organization_name", "category", "procurement_number",
        "transparency_link", "valor_global_contrato", "valor_acumulado_contrato",
        "valor_utilizado_pi_contrato", "valor_incluido_contrato", "source_updated_at",
        "ingested_at",
        "ingestion_id",
    ),
    "gold.vw_project_commitment_current": (
        "project_id", "commitment_key", "commitment_number", "emission_date", "issuing_ug",
        "source_system", "source_base", "expense_nature", "creditor_name", "commitment_description",
        "valor_empenho", "aliquidar", "liquidado", "pago", "rpinscrito", "rpaliquidar",
        "rpaliquidado", "rppago", "source_updated_at", "ingested_at", "ingestion_id",
    ),
    "gold.vw_project_commitment_totals_current": (
        "project_id", "valor_empenho", "aliquidar", "liquidado", "pago", "rpinscrito",
        "rpaliquidar", "rpaliquidado", "rppago", "commitment_count", "source_updated_at",
        "ingested_at", "ingestion_id",
    ),
    "gold.vw_project_execution_current": (
        "project_id", "id_execucao_fisica", "instrument", "physical_execution_percentage",
        "execution_registration_at", "execution_start_date", "execution_end_date",
        "instrument_creation_date", "source_update_date", "execution_form", "indicators", "reasons",
        "source_record_count", "source_updated_at", "ingested_at", "ingestion_id",
    ),
    "gold.vw_project_status_history_current": (
        "project_id", "semantic_key", "event_date", "source_status", "justification",
        "treatment_indicator", "treatment_phase", "source_event_count", "source_event_ids",
        "source_updated_at", "ingested_at", "ingestion_id",
    ),
    "gold.vw_project_feasibility_study_current": (
        "project_id", "study_key", "study_type", "study_specification", "source_updated_at",
        "ingested_at", "ingestion_id",
    ),
    "gold.vw_project_coverage_current": (
        "project_id", "section_name", "source_record_count", "display_record_count", "has_data",
        "coverage_status", "project_feasibility_study_indicator", "source_updated_at",
        "ingested_at",
        "ingestion_id",
    ),
}

DETAIL_ORDER_BY: dict[str, str] = {
    "gold.vw_project_detail_current": "project_id",
    "gold.vw_project_participant_current": (
        "participant_role, organization_name NULLS LAST, organization_cnpj NULLS LAST"
    ),
    "gold.vw_project_location_current": (
        "municipality_name NULLS LAST, ibge_code NULLS LAST, geometry_id NULLS LAST, "
        "latitude NULLS LAST, longitude NULLS LAST"
    ),
    "gold.vw_project_investment_current": "funding_source_name NULLS LAST",
    "gold.vw_project_axis_type_current": (
        "axis_name NULLS LAST, type_name NULLS LAST, subtype_name NULLS LAST"
    ),
    "gold.vw_project_ppa_current": "ppa_type NULLS LAST, ppa_description NULLS LAST",
    "gold.vw_project_restriction_area_current": "restriction_area NULLS LAST",
    "gold.vw_project_photo_indicator_current": "ind_foto NULLS LAST",
    "gold.vw_project_contract_current": "validity_end_date DESC NULLS LAST, contract_source_id",
    "gold.vw_project_commitment_current": "emission_date DESC NULLS LAST, commitment_key",
    "gold.vw_project_commitment_totals_current": "project_id",
    "gold.vw_project_execution_current": (
        "source_update_date DESC NULLS LAST, execution_registration_at DESC NULLS LAST, "
        "id_execucao_fisica"
    ),
    "gold.vw_project_status_history_current": "event_date DESC NULLS LAST, semantic_key",
    "gold.vw_project_feasibility_study_current": (
        "study_type NULLS LAST, study_specification NULLS LAST, study_key"
    ),
    "gold.vw_project_coverage_current": "section_name",
}


@dataclass(frozen=True)
class ProjectDetailData:
    """Coleções independentes de uma única obra no snapshot Gold atual."""

    project_id: str
    sections: dict[str, pd.DataFrame]
    errors: dict[str, GoldError] = field(default_factory=dict)


def _project_query(view_name: str, project_id: str) -> pd.DataFrame:
    if view_name not in CURRENT_VIEWS or view_name not in DETAIL_VIEW_COLUMNS:
        raise GoldQueryError("View Gold não permitida.")

    columns = DETAIL_VIEW_COLUMNS[view_name]
    select_list = ", ".join(columns)
    query = (
        f"SELECT {select_list} FROM {view_name} "
        f"WHERE project_id = :project_id ORDER BY {DETAIL_ORDER_BY[view_name]}"
    )
    try:
        result = _connection().query(
            query,
            ttl=QUERY_TTL_SECONDS,
            params={"project_id": project_id},
        )
    except GoldError:
        raise
    except Exception as exc:
        raise GoldQueryError(f"Falha ao consultar {view_name}.") from exc
    return _ensure_columns(result, columns)


@st.cache_data(ttl=QUERY_TTL_SECONDS, show_spinner=False)
def load_project_detail(project_id: str) -> ProjectDetailData:
    """Carrega uma obra e suas relações somente pelas views Gold atuais."""

    normalized_project_id = str(project_id).strip()
    if not normalized_project_id:
        return ProjectDetailData(project_id="", sections={})

    detail_view = "gold.vw_project_detail_current"
    detail = _project_query(detail_view, normalized_project_id)
    if detail.empty:
        return ProjectDetailData(project_id=normalized_project_id, sections={detail_view: detail})

    sections = {detail_view: detail}
    errors: dict[str, GoldError] = {}
    for view_name in DETAIL_VIEW_COLUMNS:
        if view_name == detail_view:
            continue
        try:
            sections[view_name] = _project_query(view_name, normalized_project_id)
        except GoldError as error:
            errors[view_name] = error
            sections[view_name] = pd.DataFrame(columns=DETAIL_VIEW_COLUMNS[view_name])
    return ProjectDetailData(project_id=normalized_project_id, sections=sections, errors=errors)


class GoldError(RuntimeError):
    """Erro seguro para apresentar no frontend sem expor credenciais."""

    def __init__(self, message: str, *, ingestion_id: Any = None) -> None:
        super().__init__(message)
        self.ingestion_id = ingestion_id


class GoldConfigurationError(GoldError):
    """Configuração necessária para conectar à Gold ausente."""


class GoldQueryError(GoldError):
    """Falha ao consultar uma view Gold permitida."""


@dataclass(frozen=True)
class OverviewData:
    """Conjunto mínimo de views necessário para a visão geral."""

    market_overview: pd.DataFrame
    project_location: pd.DataFrame
    status_distribution: pd.DataFrame
    snapshot_metadata: pd.DataFrame


@dataclass(frozen=True)
class FilteredMetrics:
    """Agregações SQL do recorte atual aplicado sobre as views Gold."""

    kpis: pd.DataFrame
    status_distribution: pd.DataFrame


def _connection() -> Any:
    database_url = os.getenv("GOLD_DATABASE_URL")
    if not database_url:
        raise GoldConfigurationError("GOLD_DATABASE_URL não está configurada.")

    return st.connection("gold", type="sql", url=database_url)


def _ensure_columns(frame: Any, columns: tuple[str, ...]) -> pd.DataFrame:
    result = frame.copy() if isinstance(frame, pd.DataFrame) else pd.DataFrame(frame)
    return result.reindex(columns=list(columns), fill_value=pd.NA)


def _query_view(view_name: str, *, ingestion_id: Any = None) -> pd.DataFrame:
    if view_name not in CURRENT_VIEWS or view_name not in _VIEW_QUERIES:
        raise GoldQueryError("View Gold não permitida.", ingestion_id=ingestion_id)

    query, columns = _VIEW_QUERIES[view_name]
    try:
        result = _connection().query(query, ttl=QUERY_TTL_SECONDS)
    except GoldError:
        raise
    except Exception as exc:
        raise GoldQueryError(
            f"Falha ao consultar {view_name}.",
            ingestion_id=ingestion_id,
        ) from exc

    return _ensure_columns(result, columns)


@st.cache_data(ttl=QUERY_TTL_SECONDS, show_spinner=False)
def load_overview_data() -> OverviewData:
    """Carrega somente as views atuais usadas pela visão geral."""

    snapshot = _query_view("gold.vw_snapshot_metadata_current")
    snapshot_ingestion_id = (
        snapshot.iloc[0].get("ingestion_id") if not snapshot.empty else None
    )

    try:
        market = _query_view(
            "gold.vw_market_overview_current",
            ingestion_id=snapshot_ingestion_id,
        )
        location = _query_view(
            "gold.vw_project_location_current",
            ingestion_id=snapshot_ingestion_id,
        )
        status = _query_view(
            "gold.vw_status_distribution_current",
            ingestion_id=snapshot_ingestion_id,
        )
    except GoldQueryError as exc:
        if exc.ingestion_id is None:
            raise GoldQueryError(str(exc), ingestion_id=snapshot_ingestion_id) from exc
        raise

    return OverviewData(
        market_overview=market,
        project_location=location,
        status_distribution=status,
        snapshot_metadata=snapshot,
    )


@st.cache_data(ttl=QUERY_TTL_SECONDS, show_spinner=False)
def load_filtered_metrics(
    project_ids: Sequence[str],
    *,
    municipalities: Sequence[str] = (),
) -> FilteredMetrics:
    """Calcula no PostgreSQL as métricas do recorte filtrado da visão geral."""

    normalized_project_ids = tuple(dict.fromkeys(str(value) for value in project_ids))
    normalized_municipalities = tuple(
        dict.fromkeys(str(value) for value in municipalities)
    )
    params = {
        "project_ids": list(normalized_project_ids),
        "municipalities": list(normalized_municipalities),
        "has_municipality_filter": bool(normalized_municipalities),
    }
    try:
        connection = _connection()
        kpis = connection.query(
            _FILTERED_KPI_QUERY,
            ttl=QUERY_TTL_SECONDS,
            params=params,
        )
        status = connection.query(
            _FILTERED_STATUS_QUERY,
            ttl=QUERY_TTL_SECONDS,
            params={"project_ids": list(normalized_project_ids)},
        )
    except GoldError:
        raise
    except Exception as exc:
        raise GoldQueryError("Falha ao calcular as métricas do recorte Gold.") from exc

    return FilteredMetrics(
        kpis=_ensure_columns(kpis, FILTERED_KPI_COLUMNS),
        status_distribution=_ensure_columns(status, STATUS_DISTRIBUTION_COLUMNS),
    )


@st.cache_data(ttl=QUERY_TTL_SECONDS, show_spinner=False)
def load_project_investment_data() -> pd.DataFrame:
    """Disponibiliza investimento por fonte para a página de detalhe futura."""

    return _query_view("gold.vw_project_investment_current")
