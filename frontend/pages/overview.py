"""Visão geral do mercado de obras públicas no Ceará."""

from __future__ import annotations

import html
import math
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import pandas as pd
import streamlit as st

from frontend import gold

INVESTMENT_BANDS = (
    "Até R$ 1 mi",
    "R$ 1 mi a R$ 10 mi",
    "R$ 10 mi a R$ 50 mi",
    "R$ 50 mi a R$ 200 mi",
    "Acima de R$ 200 mi",
    "Não informado",
)
NO_REGISTRATION_PERIOD = "Sem filtro"
REGISTRATION_PERIODS = (
    "Último mês",
    "Últimos 3 meses",
    "Últimos 6 meses",
    "Últimos 12 meses",
    "Ano corrente",
)
REGISTRATION_PERIOD_MONTHS = {
    "Último mês": 1,
    "Últimos 3 meses": 3,
    "Últimos 6 meses": 6,
    "Últimos 12 meses": 12,
}
FILTER_KEYS = (
    "overview_municipality",
    "overview_organization",
    "overview_status",
    "overview_axis",
    "overview_type",
    "overview_subtype",
    "overview_investment_band",
    "overview_registration_year",
    "overview_registration_period",
)

OVERVIEW_CSS = """
<style>
:root {
    --vertere-background: transparent;
    --vertere-surface: transparent;
    --vertere-muted: color-mix(in srgb, currentColor 6%, transparent);
    --vertere-ink: currentColor;
    --vertere-slate: color-mix(in srgb, currentColor 70%, transparent);
    --vertere-primary: #C44DFF;
    --vertere-primary-end: #8C1AFF;
    --vertere-primary-soft: rgba(196, 77, 255, 0.10);
    --vertere-border: color-mix(in srgb, currentColor 16%, transparent);
    --vertere-success: #16855B;
    --vertere-warning: #B56A09;
}
.overview-title {
    color: var(--vertere-ink);
    font-size: 2.25rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.1;
    margin: 0;
}
.overview-subtitle {
    color: var(--vertere-slate);
    font-size: 0.98rem;
    margin-top: 0.45rem;
}
.overview-context {
    color: var(--vertere-slate);
    font-size: 0.80rem;
    margin-top: 0.45rem;
}
.snapshot-chip {
    border: 1px solid var(--vertere-border);
    border-radius: 10px;
    color: var(--vertere-slate);
    font-size: 0.78rem;
    line-height: 1.45;
    margin-top: 0.75rem;
    padding: 0.65rem 0.8rem;
    text-align: left;
}
.snapshot-dot {
    color: var(--vertere-primary-end);
    font-size: 1rem;
    vertical-align: -0.05rem;
}
.partial-badge {
    background: var(--vertere-muted);
    border: 1px solid var(--vertere-border);
    border-radius: 9999px;
    color: var(--vertere-slate);
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.30rem 0.65rem;
}
.partial-state {
    display: block;
    margin-top: 0.75rem;
}
.partial-badge-wrap {
    display: inline-block;
    position: relative;
}
.partial-badge {
    cursor: help;
}
.partial-badge:focus-visible {
    outline: 2px solid var(--vertere-primary-end);
    outline-offset: 2px;
}
.partial-tooltip {
    background: Canvas;
    border: 1px solid color-mix(in srgb, CanvasText 18%, transparent);
    border-radius: 0.55rem;
    box-shadow: 0 0.4rem 1.2rem color-mix(in srgb, CanvasText 18%, transparent);
    color: CanvasText;
    font-size: 0.82rem;
    line-height: 1.4;
    opacity: 0;
    padding: 0.65rem 0.8rem;
    pointer-events: none;
    position: absolute;
    left: 0;
    top: calc(100% + 0.5rem);
    transform: translateY(-0.25rem);
    transition: opacity 120ms ease, transform 120ms ease;
    visibility: hidden;
    width: min(26rem, 70vw);
    z-index: 6;
}
.partial-badge-wrap:hover .partial-tooltip,
.partial-badge-wrap:focus-within .partial-tooltip {
    opacity: 1;
    pointer-events: auto;
    transform: translateY(0);
    visibility: visible;
}
.section-caption {
    color: var(--vertere-slate);
    font-size: 0.78rem;
}
.map-help-anchor {
    align-items: center;
    display: flex;
    justify-content: flex-end;
    margin-top: -2.65rem;
    min-height: 2.65rem;
    padding: 0 0.75rem 0.75rem 0;
    pointer-events: none;
    position: relative;
    z-index: 4;
}
.map-help {
    pointer-events: auto;
    position: relative;
}
.map-help-icon {
    align-items: center;
    background: Canvas;
    border: 1px solid color-mix(in srgb, CanvasText 25%, transparent);
    border-radius: 9999px;
    color: CanvasText;
    cursor: help;
    display: inline-flex;
    font-size: 0.78rem;
    font-weight: 700;
    height: 1.25rem;
    justify-content: center;
    line-height: 1;
    width: 1.25rem;
}
.map-help-icon:focus-visible {
    outline: 2px solid var(--vertere-primary-end);
    outline-offset: 2px;
}
.map-help-tooltip {
    background: Canvas;
    border: 1px solid color-mix(in srgb, CanvasText 18%, transparent);
    border-radius: 0.55rem;
    bottom: calc(100% + 0.5rem);
    box-shadow: 0 0.4rem 1.2rem color-mix(in srgb, CanvasText 18%, transparent);
    color: CanvasText;
    font-size: 0.82rem;
    line-height: 1.4;
    opacity: 0;
    padding: 0.65rem 0.8rem;
    pointer-events: none;
    position: absolute;
    right: 0;
    text-align: left;
    transform: translateY(0.25rem);
    transition: opacity 120ms ease, transform 120ms ease;
    visibility: hidden;
    width: min(26rem, 70vw);
    z-index: 5;
}
.map-help:hover .map-help-tooltip,
.map-help:focus-within .map-help-tooltip {
    opacity: 1;
    pointer-events: auto;
    transform: translateY(0);
    visibility: visible;
}
.kpi-icon {
    align-items: center;
    background: var(--vertere-primary-soft);
    border-radius: 9999px;
    color: var(--vertere-primary-end);
    display: inline-flex;
    font-size: 1.15rem;
    font-weight: 700;
    height: 2.8rem;
    justify-content: center;
    margin-bottom: 0.35rem;
    width: 2.8rem;
}
.filter-heading {
    color: var(--vertere-ink);
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--vertere-surface);
    border-color: var(--vertere-border);
    border-radius: 12px;
}
[data-testid="stDeckGlJsonChart"] button.mapboxgl-ctrl-attrib-button {
    display: none !important;
}
[data-testid="stDeckGlJsonChart"] .mapboxgl-ctrl-attrib {
    display: none !important;
}
[data-testid="stVerticalBlock"]:has(.map-help-anchor) {
    position: relative;
}
[data-testid="stVerticalBlock"]:has(.map-help-anchor) .map-help-anchor {
    bottom: 0.9rem;
    margin-top: 0;
    min-height: 0;
    padding: 0 0.75rem 0 0;
    position: absolute;
    right: 0;
    width: 100%;
}
</style>
"""


@dataclass(frozen=True)
class FilterState:
    municipality: tuple[str, ...] = ()
    organization: tuple[str, ...] = ()
    status: tuple[str, ...] = ()
    axis: tuple[str, ...] = ()
    intervention_type: tuple[str, ...] = ()
    subtype: tuple[str, ...] = ()
    investment_band: tuple[str, ...] = ()
    registration_year: tuple[str, ...] = ()
    registration_period: tuple[str, ...] = ()

    @property
    def is_active(self) -> bool:
        return any(
            (
                self.municipality,
                self.organization,
                self.status,
                self.axis,
                self.intervention_type,
                self.subtype,
                self.investment_band,
                self.registration_year,
                self.registration_period,
            )
        )


def _is_null(value: Any) -> bool:
    if value is None or value is pd.NA:
        return True
    try:
        missing = pd.isna(value)
    except (TypeError, ValueError):
        return False
    if isinstance(missing, bool):
        return missing
    return False


def _display_text(value: Any) -> str:
    if _is_null(value):
        return "Não informado"
    if isinstance(value, pd.Timestamp | datetime | date):
        return value.strftime("%d/%m/%Y")
    text = str(value).strip()
    return text or "Não informado"


def _format_datetime(value: Any) -> str:
    if _is_null(value):
        return "Não informado"
    parsed = pd.to_datetime(value, errors="coerce")
    if _is_null(parsed):
        return _display_text(value)
    return parsed.strftime("%d/%m/%Y %H:%M")


def _snapshot_reference_date(snapshot: pd.DataFrame) -> date:
    values = pd.to_datetime(
        snapshot.get("source_updated_at", pd.Series(dtype="object")),
        errors="coerce",
        utc=True,
    ).dropna()
    if not values.empty:
        return values.iloc[0].date()
    return date.today()


def _ensure_frame(value: Any, columns: tuple[str, ...]) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        result = value.copy()
    elif value is None:
        result = pd.DataFrame()
    else:
        result = pd.DataFrame(value)
    for column in columns:
        if column not in result.columns:
            result[column] = pd.NA
    return result


def _column_values(frame: pd.DataFrame, column: str) -> list[str]:
    if column not in frame.columns:
        return []
    values = {_display_text(value) for value in frame[column].tolist()}
    return sorted(
        values,
        key=lambda item: (item == "Não informado", item.casefold()),
    )


def _split_aggregated(value: Any) -> list[str]:
    if _is_null(value):
        return ["Não informado"]
    return [
        part.strip()
        for part in re.split(r"\s*(?:,|;|\|)\s*", str(value))
        if part.strip()
    ] or ["Não informado"]


def _municipality_options(
    market: pd.DataFrame,
    location: pd.DataFrame,
) -> list[str]:
    if "municipality_name" in location.columns and not location.empty:
        return _column_values(location, "municipality_name")
    values: set[str] = set()
    if "municipality_names" in market.columns:
        for value in market["municipality_names"].tolist():
            values.update(_split_aggregated(value))
    return sorted(values, key=lambda item: (item == "Não informado", item.casefold()))


def _investment_band(value: Any) -> str:
    if _is_null(value):
        return "Não informado"
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return "Não informado"
    if not math.isfinite(amount):
        return "Não informado"
    if amount <= 1_000_000:
        return "Até R$ 1 mi"
    if amount <= 10_000_000:
        return "R$ 1 mi a R$ 10 mi"
    if amount <= 50_000_000:
        return "R$ 10 mi a R$ 50 mi"
    if amount <= 200_000_000:
        return "R$ 50 mi a R$ 200 mi"
    return "Acima de R$ 200 mi"


def _year_options(frame: pd.DataFrame) -> list[str]:
    if "registration_year" not in frame.columns:
        return []
    years = {_registration_year_label(value) for value in frame["registration_year"].tolist()}
    return sorted(years, key=lambda item: (item == "Não informado", item))


def _registration_year_label(value: Any) -> str:
    if _is_null(value):
        return "Não informado"
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return _display_text(value)


def _reset_filter_state() -> None:
    for key in FILTER_KEYS:
        st.session_state[key] = (
            NO_REGISTRATION_PERIOD if key == "overview_registration_period" else []
        )


def _filter_label(label: str, key: str) -> str:
    return label


def _render_filters(
    market: pd.DataFrame,
    location: pd.DataFrame,
) -> FilterState:
    st.sidebar.markdown('<div class="filter-heading">Filtros</div>', unsafe_allow_html=True)
    municipality_options = _municipality_options(market, location)
    organization_options = _column_values(market, "organization_name")
    status_options = _column_values(market, "source_status")
    axis_options = _column_values(market, "axis_name")
    type_options = _column_values(market, "type_name")
    subtype_options = _column_values(market, "subtype_name")
    year_options = _year_options(market)

    with st.sidebar.form("overview_filters"):
        municipalities = st.multiselect(
            _filter_label("Município", "overview_municipality"),
            municipality_options,
            key="overview_municipality",
        )
        organizations = st.multiselect(
            _filter_label("Organização responsável", "overview_organization"),
            organization_options,
            key="overview_organization",
        )
        statuses = st.multiselect(
            _filter_label("Situação original", "overview_status"),
            status_options,
            key="overview_status",
        )
        axes = st.multiselect(
            _filter_label("Eixo", "overview_axis"),
            axis_options,
            key="overview_axis",
        )
        intervention_types = st.multiselect(
            _filter_label("Tipo", "overview_type"),
            type_options,
            key="overview_type",
        )
        subtypes = st.multiselect(
            _filter_label("Subtipo", "overview_subtype"),
            subtype_options,
            key="overview_subtype",
        )
        investment_bands = st.multiselect(
            _filter_label("Faixa de investimento", "overview_investment_band"),
            list(INVESTMENT_BANDS),
            key="overview_investment_band",
        )
        years = st.multiselect(
            _filter_label("Ano de cadastro", "overview_registration_year"),
            year_options,
            key="overview_registration_year",
        )
        registration_period = st.selectbox(
            _filter_label(
                "Período da data de cadastro",
                "overview_registration_period",
            ),
            [NO_REGISTRATION_PERIOD, *REGISTRATION_PERIODS],
            key="overview_registration_period",
        )
        st.form_submit_button(
            "Aplicar filtros",
            type="primary",
            use_container_width=True,
        )

    st.sidebar.button(
        "Limpar filtros",
        key="overview_clear_filters",
        on_click=_reset_filter_state,
        use_container_width=True,
    )
    return FilterState(
        municipality=tuple(municipalities),
        organization=tuple(organizations),
        status=tuple(statuses),
        axis=tuple(axes),
        intervention_type=tuple(intervention_types),
        subtype=tuple(subtypes),
        investment_band=tuple(investment_bands),
        registration_year=tuple(years),
        registration_period=(
            ()
            if registration_period == NO_REGISTRATION_PERIOD
            else (registration_period,)
        ),
    )


def _project_key(value: Any) -> str:
    return "" if _is_null(value) else str(value)


def _selected_mask(frame: pd.DataFrame, column: str, selected: tuple[str, ...]) -> pd.Series:
    if not selected:
        return pd.Series(True, index=frame.index)
    if column not in frame.columns:
        return pd.Series(False, index=frame.index)
    return frame[column].map(_display_text).isin(selected)


def _registration_period_mask(
    market: pd.DataFrame,
    selected: tuple[str, ...],
    reference_date: date | None = None,
) -> pd.Series:
    if not selected:
        return pd.Series(True, index=market.index)
    if "registration_date" not in market.columns:
        return pd.Series(False, index=market.index)

    registered = pd.to_datetime(
        market["registration_date"],
        errors="coerce",
        utc=True,
    ).dt.tz_localize(None).dt.normalize()
    reference = pd.Timestamp(reference_date or date.today()).normalize()
    mask = pd.Series(False, index=market.index)
    for period in selected:
        months = REGISTRATION_PERIOD_MONTHS.get(period)
        if months is not None:
            start = reference - pd.DateOffset(months=months)
            mask |= registered.between(start, reference, inclusive="both")
        elif period == "Ano corrente":
            mask |= registered.dt.year.eq(reference.year)
    return mask.fillna(False)


def _municipality_mask(
    market: pd.DataFrame,
    location: pd.DataFrame,
    selected: tuple[str, ...],
) -> pd.Series:
    if not selected:
        return pd.Series(True, index=market.index)
    if not location.empty and "project_id" in location.columns:
        location_names = location.get("municipality_name", pd.Series(pd.NA, index=location.index))
        matching_locations = location_names.map(_display_text).isin(selected)
        selected_ids = {
            _project_key(value)
            for value in location.loc[matching_locations, "project_id"]
        }
        return market["project_id"].map(_project_key).isin(selected_ids)
    if "municipality_names" not in market.columns:
        return pd.Series(False, index=market.index)
    return market["municipality_names"].map(
        lambda value: bool(set(_split_aggregated(value)).intersection(selected))
    )


def _apply_filters(
    market: pd.DataFrame,
    location: pd.DataFrame,
    filters: FilterState,
    *,
    reference_date: date | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    mask = _municipality_mask(market, location, filters.municipality)
    for column, selected in (
        ("organization_name", filters.organization),
        ("source_status", filters.status),
        ("axis_name", filters.axis),
        ("type_name", filters.intervention_type),
        ("subtype_name", filters.subtype),
    ):
        mask &= _selected_mask(market, column, selected)

    if filters.investment_band:
        bands = market.get(
            "planned_investment_amount",
            pd.Series(pd.NA, index=market.index),
        ).map(_investment_band)
        mask &= bands.isin(filters.investment_band)

    if filters.registration_year:
        years = market.get(
            "registration_year",
            pd.Series(pd.NA, index=market.index),
        ).map(_registration_year_label)
        mask &= years.isin(filters.registration_year)

    mask &= _registration_period_mask(
        market,
        filters.registration_period,
        reference_date,
    )

    filtered_market = market.loc[mask].copy()
    if location.empty or "project_id" not in location.columns:
        return filtered_market, location.copy()

    filtered_ids = {_project_key(value) for value in filtered_market["project_id"]}
    location_mask = location["project_id"].map(_project_key).isin(filtered_ids)
    if filters.municipality:
        location_mask &= location.get(
            "municipality_name",
            pd.Series(pd.NA, index=location.index),
        ).map(_display_text).isin(filters.municipality)
    filtered_location = location.loc[
        location_mask
    ].copy()
    return filtered_market, filtered_location


def _filtered_project_ids(market: pd.DataFrame) -> tuple[str, ...]:
    if "project_id" not in market.columns:
        return ()
    return tuple(
        dict.fromkeys(
            _project_key(value)
            for value in market["project_id"].tolist()
            if _project_key(value)
        )
    )


def _format_count(value: Any) -> str:
    if _is_null(value):
        return "Não informado"
    try:
        return f"{float(value):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "Não informado"


def _format_currency(value: Any) -> str:
    if _is_null(value):
        return "Não informado"
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return "Não informado"
    if not math.isfinite(amount):
        return "Não informado"
    if abs(amount) >= 1_000_000_000:
        return f"R$ {_format_br_number(amount / 1_000_000_000, 2)} bi"
    if abs(amount) >= 1_000_000:
        return f"R$ {_format_br_number(amount / 1_000_000, 2)} mi"
    if abs(amount) >= 1_000:
        return f"R$ {_format_br_number(amount / 1_000, 1)} mil"
    return f"R$ {_format_br_number(amount, 2)}"


def _format_br_number(value: float, decimals: int) -> str:
    formatted = f"{value:,.{decimals}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def _render_styles() -> None:
    st.markdown(OVERVIEW_CSS, unsafe_allow_html=True)


def _render_header(snapshot: pd.DataFrame) -> None:
    snapshot_row = snapshot.iloc[0] if not snapshot.empty else {}
    title_column, snapshot_column = st.columns([5, 2])
    with title_column:
        st.markdown(
            '<h1 class="overview-title">Inteligência de Obras Públicas — Ceará</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="overview-subtitle">Obras de construção no Ceará '
            '<span class="snapshot-dot">•</span> fonte ObrasGov</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="overview-context">UF principal = CE · natureza = Obra · '
            'espécie = Construção</div>',
            unsafe_allow_html=True,
        )
    with snapshot_column:
        source_updated_at = _format_datetime(snapshot_row.get("source_updated_at"))
        ingested_at = _format_datetime(snapshot_row.get("ingested_at"))
        chip = (
            '<div class="snapshot-chip"><strong>Snapshot atual</strong> '
            '<span class="snapshot-dot">•</span><br>'
            f"Fonte: {html.escape(source_updated_at)}<br>"
            f"Ingestão: {html.escape(ingested_at)}</div>"
        )
        st.markdown(chip, unsafe_allow_html=True)


def _render_partial_state(
    market: pd.DataFrame,
    location: pd.DataFrame,
    snapshot: pd.DataFrame,
) -> None:
    reasons: list[str] = []
    if snapshot.empty:
        reasons.append("metadados do snapshot não disponíveis")
    if market.empty:
        return
    if location.empty:
        reasons.append("localização não disponível")
    elif {"latitude", "longitude"}.issubset(location.columns):
        coordinates = location[["latitude", "longitude"]].notna().all(axis=1)
        if not coordinates.all():
            reasons.append("parte dos municípios não possui coordenadas")
    if "planned_investment_amount" in market.columns:
        if market["planned_investment_amount"].isna().any():
            reasons.append("parte dos investimentos previstos está sem valor")
    if not reasons:
        return
    reason_text = "; ".join(reasons).capitalize() + "."
    escaped_reason = html.escape(reason_text)
    st.markdown(
        '<div class="partial-state">'
        '<span class="partial-badge-wrap">'
        '<span class="partial-badge" tabindex="0" '
        'aria-describedby="partial-state-tooltip">Dados parciais</span>'
        f'<span id="partial-state-tooltip" class="partial-tooltip" role="tooltip">'
        f"{escaped_reason}</span>"
        "</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.caption(reason_text)


def _render_kpis(metrics: pd.DataFrame) -> None:
    row = metrics.iloc[0] if not metrics.empty else {}
    total_projects = _format_count(row.get("project_count"))
    investment = _format_currency(row.get("planned_investment_amount"))
    municipalities = _format_count(row.get("municipality_count"))
    execution = _format_count(row.get("execution_project_count"))
    metrics = (
        (
            "▦",
            "Total de obras",
            total_projects,
            "Contagem distinta de projetos no recorte filtrado.",
        ),
        (
            "R$",
            "Investimento previsto",
            investment,
            "Soma do investimento previsto no recorte filtrado.",
        ),
        (
            "⌖",
            "Municípios alcançados",
            municipalities,
            "Contagem distinta de municípios associados ao recorte filtrado.",
        ),
        (
            "◒",
            "Obras em execução",
            execution,
            "Contagem distinta de projetos com a situação original Em execução "
            "no recorte filtrado.",
        ),
    )
    columns = st.columns(4, gap="medium")
    for column, (icon, label, value, help_text) in zip(columns, metrics, strict=True):
        with column:
            with st.container(border=True):
                st.markdown(f'<div class="kpi-icon">{icon}</div>', unsafe_allow_html=True)
                st.metric(label, value, help=help_text)


def _render_map(location: pd.DataFrame) -> None:
    st.subheader("Distribuição territorial")
    if location.empty or not {"latitude", "longitude"}.issubset(location.columns):
        st.info("Não há municípios associados ao filtro atual.")
        return
    map_data = location[["latitude", "longitude"]].copy()
    map_data["latitude"] = pd.to_numeric(map_data["latitude"], errors="coerce")
    map_data["longitude"] = pd.to_numeric(map_data["longitude"], errors="coerce")
    map_data = map_data.dropna(subset=["latitude", "longitude"])
    if map_data.empty:
        st.info("Não há coordenadas disponíveis para o filtro atual.")
        return
    with st.container(key="overview_map_visual"):
        st.map(map_data, latitude="latitude", longitude="longitude", use_container_width=True)
        missing_coordinates = len(location) - len(map_data)
        coordinate_note = (
            f" {missing_coordinates} registro(s) sem coordenadas não aparece(m) no mapa."
            if missing_coordinates
            else ""
        )
        help_text = (
            "Pontos representam municípios com coordenadas disponíveis. "
            "O investimento previsto permanece identificado na tabela."
            f"{coordinate_note}"
        )
        st.markdown(
            '<div class="map-help-anchor">'
            '<div class="map-help">'
            '<span class="map-help-icon" role="img" tabindex="0" '
            'aria-label="Informações do mapa">i</span>'
            f'<div class="map-help-tooltip" role="tooltip">{html.escape(help_text)}</div>'
            "</div></div>",
            unsafe_allow_html=True,
        )


def _status_frame(status_distribution: pd.DataFrame) -> pd.DataFrame:
    result = _ensure_frame(status_distribution, gold.STATUS_DISTRIBUTION_COLUMNS)
    result["source_status"] = result["source_status"].map(_display_text)
    result["project_count"] = pd.to_numeric(result["project_count"], errors="coerce")
    return result.dropna(subset=["project_count"])


def _render_status(
    status_distribution: pd.DataFrame,
) -> None:
    st.subheader("Projetos por situação")
    chart_data = _status_frame(status_distribution)
    if chart_data.empty:
        st.info("Não há situação original disponível para o filtro atual.")
        return
    chart_data = chart_data.sort_values("project_count", ascending=True)
    try:
        import plotly.express as px

        figure = px.bar(
            chart_data,
            x="project_count",
            y="source_status",
            orientation="h",
            text="project_count",
            labels={"project_count": "Projetos", "source_status": ""},
        )
        figure.update_traces(
            marker_color="#8C1AFF",
            textposition="outside",
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
        figure.update_layout(
            height=330,
            margin={"l": 0, "r": 45, "t": 10, "b": 10},
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            xaxis={
                "showgrid": True,
                "gridcolor": "rgba(128, 128, 128, 0.25)",
                "title": None,
            },
            yaxis={"title": None},
        )
        st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})
    except ImportError:
        fallback = chart_data.set_index("source_status")[["project_count"]]
        st.bar_chart(fallback)
    st.caption(
        "Contagem do recorte filtrado; situações preservadas conforme os valores originais."
    )


def _render_table(market: pd.DataFrame) -> None:
    st.subheader("Obras para análise")
    if market.empty:
        st.info("Nenhum projeto corresponde aos filtros atuais.")
        return
    table = pd.DataFrame(
        {
            "Projeto": market.get("project_name", pd.Series(pd.NA, index=market.index)).map(
                _display_text
            ),
            "Município": market.get(
                "municipality_names",
                pd.Series(pd.NA, index=market.index),
            ).map(_display_text),
            "Organização responsável": market.get(
                "organization_name",
                pd.Series(pd.NA, index=market.index),
            ).map(_display_text),
            "Situação original": market.get(
                "source_status",
                pd.Series(pd.NA, index=market.index),
            ).map(_display_text),
            "Investimento previsto": market.get(
                "planned_investment_amount",
                pd.Series(pd.NA, index=market.index),
            ).map(_format_currency),
        }
    )
    event = st.dataframe(
        table,
        hide_index=True,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Projeto": st.column_config.TextColumn("Projeto", width="large"),
            "Município": st.column_config.TextColumn("Município", width="medium"),
            "Organização responsável": st.column_config.TextColumn(
                "Organização responsável",
                width="medium",
            ),
            "Situação original": st.column_config.TextColumn(
                "Situação original",
                width="small",
            ),
            "Investimento previsto": st.column_config.TextColumn(
                "Investimento previsto",
                width="medium",
            ),
        },
    )
    selected_rows = getattr(getattr(event, "selection", None), "rows", [])
    if selected_rows:
        selected_project = market.iloc[selected_rows[0]].get("project_id")
        st.session_state["selected_project_id"] = selected_project
        st.info(
            "Projeto selecionado. O detalhe completo permanece fora do escopo da SPEC-001."
        )


def _render_error(error: gold.GoldError) -> None:
    st.error("Não foi possível carregar o snapshot atual da Gold.")
    if isinstance(error, gold.GoldConfigurationError):
        st.caption("Configure GOLD_DATABASE_URL para conectar ao banco somente leitura.")
    else:
        st.caption("Verifique a disponibilidade do banco e tente novamente.")
    if error.ingestion_id is not None:
        st.caption(f"Ingestion ID: {_display_text(error.ingestion_id)}")
    if st.button("Tentar novamente", key="overview_retry"):
        st.cache_data.clear()
        st.rerun()


def main() -> None:
    _render_styles()
    try:
        with st.spinner("Carregando snapshot atual..."):
            data = gold.load_overview_data()
    except gold.GoldError as error:
        _render_error(error)
        return
    except Exception:
        _render_error(gold.GoldQueryError("Falha inesperada ao consultar a Gold."))
        return

    market = _ensure_frame(data.market_overview, gold.MARKET_OVERVIEW_COLUMNS)
    location = _ensure_frame(data.project_location, gold.PROJECT_LOCATION_COLUMNS)
    snapshot = _ensure_frame(data.snapshot_metadata, gold.SNAPSHOT_METADATA_COLUMNS)

    _render_header(snapshot)
    filters = _render_filters(market, location)
    filtered_market, filtered_location = _apply_filters(
        market,
        location,
        filters,
        reference_date=_snapshot_reference_date(snapshot),
    )
    _render_partial_state(filtered_market, filtered_location, snapshot)

    if filtered_market.empty:
        st.info(
            "Nenhum projeto corresponde aos filtros atuais. "
            "Limpe ou ajuste os filtros para continuar."
        )
        return

    try:
        filtered_metrics = gold.load_filtered_metrics(
            _filtered_project_ids(filtered_market),
            municipalities=filters.municipality,
        )
    except gold.GoldError as error:
        _render_error(error)
        return

    _render_kpis(filtered_metrics.kpis)
    map_column, status_column = st.columns([1.1, 1], gap="large")
    with map_column:
        _render_map(filtered_location)
    with status_column:
        _render_status(filtered_metrics.status_distribution)
    _render_table(filtered_market)
    st.caption(
        "KPIs, distribuição, mapa e tabela refletem os filtros atuais sobre o snapshot Gold. "
        "Situações preservadas da fonte, sem classificação comercial."
    )


main()
