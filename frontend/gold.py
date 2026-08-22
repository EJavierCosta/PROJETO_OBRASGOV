"""Acesso somente leitura às views atuais da camada Gold."""

from __future__ import annotations

import os
from dataclasses import dataclass
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
    "latitude",
    "longitude",
    "planned_investment_amount",
)

STATUS_DISTRIBUTION_COLUMNS = ("source_status", "project_count")
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
def load_project_investment_data() -> pd.DataFrame:
    """Disponibiliza investimento por fonte para a página de detalhe futura."""

    return _query_view("gold.vw_project_investment_current")
