"""Detalhe executivo de um projeto, consumindo somente a Gold atual."""

from __future__ import annotations

import html
import math
from collections.abc import Mapping
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

from frontend import gold

DETAIL_VIEW = "gold.vw_project_detail_current"
DETAIL_PROJECT_SESSION_KEY = "_detail_project_id"

DETAIL_CSS = """
<style>
:root {
    --detail-ink: #14161A;
    --detail-slate: #4B5768;
    --detail-border: #E5E7EB;
    --detail-primary: #8C1AFF;
    --detail-primary-soft: rgba(196, 77, 255, 0.10);
    --detail-muted: #F9FAFB;
    --detail-warning: #B56A09;
}
.detail-title-row {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    gap: 0.7rem;
    margin-top: 0.35rem;
}
.detail-badge-row {
    align-items: center;
    display: flex;
    flex-wrap: nowrap;
    gap: 0.5rem;
    margin-top: 0.55rem;
}
.detail-title {
    color: var(--detail-ink);
    font-size: clamp(1.75rem, 3vw, 2.45rem);
    font-weight: 700;
    letter-spacing: -0.025em;
    line-height: 1.08;
    margin: 0;
}
.detail-title-chip,
.detail-status-chip,
.detail-count-chip,
.detail-partial-chip {
    border-radius: 9999px;
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 600;
    line-height: 1.35;
    padding: 0.34rem 0.68rem;
    white-space: nowrap;
}
.detail-title-chip {
    background: var(--detail-primary-soft);
    color: var(--detail-primary);
}
.detail-status-chip {
    background: var(--detail-primary-soft);
    color: var(--detail-primary);
}
.detail-count-chip {
    background: var(--detail-muted);
    border: 1px solid var(--detail-border);
    color: var(--detail-slate);
}
.detail-partial-chip {
    background: rgba(181, 106, 9, 0.12);
    color: var(--detail-warning);
}
.detail-meta {
    color: var(--detail-slate);
    font-size: 0.82rem;
    line-height: 1.6;
    margin-top: 0.55rem;
}
.detail-meta-dot {
    color: var(--detail-primary);
    padding: 0 0.45rem;
}
.detail-snapshot {
    border: 1px solid var(--detail-border);
    border-radius: 10px;
    color: var(--detail-slate);
    font-size: 0.78rem;
    line-height: 1.5;
    padding: 0.68rem 0.8rem;
}
.detail-snapshot strong {
    color: var(--detail-ink);
}
.detail-section-heading {
    align-items: baseline;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
}
.detail-section-heading h2 {
    color: var(--detail-ink);
    font-size: 1.02rem;
    font-weight: 700;
    line-height: 1.25;
    margin: 0;
    padding: 0;
}
.detail-section-note {
    color: var(--detail-slate);
    font-size: 0.75rem;
}
.detail-kpi-card {
    background: Canvas;
    border: 1px solid var(--detail-border);
    border-radius: 12px;
    min-height: 6.8rem;
    margin-bottom: 0.75rem;
    padding: 0.9rem 1rem;
}
.detail-kpi-icon {
    align-items: center;
    background: var(--detail-primary-soft);
    border-radius: 9999px;
    color: var(--detail-primary);
    display: inline-flex;
    font-size: 1.15rem;
    font-weight: 700;
    height: 2.65rem;
    justify-content: center;
    margin-bottom: 0.28rem;
    width: 2.65rem;
}
.detail-kpi-label {
    color: var(--detail-slate);
    font-size: 0.78rem;
    font-weight: 600;
    margin-top: 0.1rem;
}
.detail-kpi-value {
    color: var(--detail-ink);
    font-size: 1.65rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.12;
    margin-top: 0.2rem;
}
.detail-location-summary {
    display: grid;
    gap: 0.55rem;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    margin-bottom: 0.65rem;
}
.detail-location-stat {
    background: var(--detail-muted);
    border: 1px solid var(--detail-border);
    border-radius: 8px;
    padding: 0.58rem 0.68rem;
}
.detail-location-stat strong,
.detail-location-stat span {
    display: block;
}
.detail-location-stat strong {
    color: var(--detail-ink);
    font-size: 1.05rem;
    line-height: 1.15;
}
.detail-location-stat span {
    color: var(--detail-slate);
    font-size: 0.7rem;
    margin-top: 0.18rem;
}
.detail-location-list {
    display: grid;
    gap: 0.55rem;
}
.detail-location-record {
    border: 1px solid var(--detail-border);
    border-radius: 8px;
    padding: 0.62rem 0.7rem;
}
.detail-location-record-title {
    color: var(--detail-ink);
    font-size: 0.78rem;
    font-weight: 700;
    line-height: 1.3;
}
.detail-location-record-fields {
    display: grid;
    gap: 0.48rem 0.8rem;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    margin-top: 0.48rem;
}
.detail-location-field-label,
.detail-location-field-value {
    display: block;
}
.detail-location-field-label {
    color: var(--detail-slate);
    font-size: 0.68rem;
    line-height: 1.2;
}
.detail-location-field-value {
    color: var(--detail-ink);
    font-size: 0.76rem;
    line-height: 1.3;
    margin-top: 0.12rem;
    overflow-wrap: anywhere;
}
.detail-map-help-anchor {
    align-items: center;
    display: flex;
    justify-content: flex-end;
    margin-top: -2.35rem;
    min-height: 2.35rem;
    padding: 0 0.75rem 0.65rem 0;
    pointer-events: none;
    position: relative;
    z-index: 4;
}
.detail-map-help {
    pointer-events: auto;
    position: relative;
}
.detail-map-help-icon {
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
.detail-map-help-icon:focus-visible {
    outline: 2px solid var(--detail-primary);
    outline-offset: 2px;
}
.detail-map-help-tooltip {
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
    width: min(18rem, calc(100vw - 2rem));
    z-index: 5;
}
.detail-map-help:hover .detail-map-help-tooltip,
.detail-map-help:focus-within .detail-map-help-tooltip {
    opacity: 1;
    pointer-events: auto;
    transform: translateY(0);
    visibility: visible;
}
[data-testid="stDeckGlJsonChart"] button.mapboxgl-ctrl-attrib-button,
[data-testid="stDeckGlJsonChart"] .mapboxgl-ctrl-attrib {
    display: none !important;
}
[data-testid="stVerticalBlock"]:has(.detail-map-help-anchor) {
    position: relative;
}
[data-testid="stVerticalBlock"]:has(.detail-map-help-anchor) .detail-map-help-anchor {
    bottom: 0.9rem;
    margin-top: 0;
    min-height: 0;
    padding: 0 0.75rem 0 0;
    position: absolute;
    right: 0;
    width: 100%;
}
.detail-pair-grid {
    display: grid;
    gap: 0.9rem 1.25rem;
    grid-template-columns: repeat(2, minmax(0, 1fr));
}
.detail-pair {
    border-bottom: 1px solid var(--detail-border);
    min-width: 0;
    padding-bottom: 0.65rem;
}
.detail-pair-label {
    color: var(--detail-slate);
    display: block;
    font-size: 0.74rem;
    line-height: 1.25;
    margin-bottom: 0.22rem;
}
.detail-pair-value {
    color: var(--detail-ink);
    display: block;
    font-size: 0.88rem;
    line-height: 1.4;
    overflow-wrap: anywhere;
}
.detail-prose {
    background: var(--detail-muted);
    border-left: 3px solid var(--detail-primary);
    border-radius: 0 8px 8px 0;
    color: var(--detail-ink);
    font-size: 0.9rem;
    line-height: 1.55;
    margin-bottom: 1rem;
    padding: 0.75rem 0.9rem;
}
.detail-bar-row {
    align-items: center;
    display: grid;
    gap: 0.6rem;
    grid-template-columns: minmax(8rem, 1.1fr) minmax(8rem, 3fr) minmax(5rem, 0.8fr);
    margin: 0.72rem 0;
}
.detail-bar-label,
.detail-bar-value,
.detail-bar-share {
    color: var(--detail-slate);
    font-size: 0.8rem;
}
.detail-bar-value,
.detail-bar-share {
    color: var(--detail-ink);
    font-variant-numeric: tabular-nums;
    text-align: right;
}
.detail-bar-track {
    background: #EEE7FF;
    border-radius: 9999px;
    height: 0.62rem;
    overflow: hidden;
}
.detail-bar-fill {
    background: linear-gradient(90deg, #C44DFF, #8C1AFF);
    border-radius: inherit;
    height: 100%;
    min-width: 0.35rem;
}
.detail-total-card {
    background: var(--detail-muted);
    border: 1px solid var(--detail-border);
    border-radius: 10px;
    margin: 0.45rem;
    min-height: 0;
    padding: 0.65rem 0.8rem;
    text-align: center;
}
.detail-total-label {
    color: var(--detail-slate);
    font-size: 0.78rem;
    line-height: 1.25;
}
.detail-total-value {
    color: var(--detail-ink);
    font-size: 1.35rem;
    font-weight: 700;
    line-height: 1.1;
    margin: 0.14rem 0 0.18rem;
}
.detail-execution-percent-card {
    padding-left: 0.65rem;
    padding-right: 0.65rem;
}
.detail-execution-record-marker {
    display: none;
}
[data-testid="stVerticalBlock"][class*="st-key-detail_execution_record_"] {
    padding: 0.25rem 0.25rem 0.85rem;
}
[data-testid="stVerticalBlock"][class*="st-key-detail_execution_record_"] .detail-record-title {
    margin: 0.15rem 0.35rem 0.65rem;
}
.detail-record-title {
    color: var(--detail-ink);
    font-size: 0.86rem;
    font-weight: 700;
    margin-bottom: 0.55rem;
}
.detail-finance-group {
    margin-top: 0.8rem;
}
.detail-finance-group:first-child {
    margin-top: 0;
}
.detail-finance-label {
    color: var(--detail-slate);
    font-size: 0.78rem;
    font-weight: 600;
    margin-bottom: 0.55rem;
}
.detail-finance-grid {
    display: grid;
    gap: 0.75rem;
    grid-template-columns: repeat(4, minmax(0, 1fr));
}
.detail-finance-item {
    border-left: 2px solid var(--detail-primary);
    padding-left: 0.7rem;
}
.detail-finance-item-label {
    color: var(--detail-slate);
    display: block;
    font-size: 0.74rem;
}
.detail-finance-item-value {
    color: var(--detail-ink);
    display: block;
    font-size: 1.05rem;
    font-weight: 700;
    margin-top: 0.2rem;
}
.detail-footer {
    border-top: 1px solid var(--detail-border);
    color: var(--detail-slate);
    font-size: 0.74rem;
    line-height: 1.55;
    margin-top: 1rem;
    padding: 0.85rem 0.2rem 0.25rem;
}
@media (max-width: 900px) {
    .detail-pair-grid,
    .detail-finance-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .detail-location-record-fields {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .detail-bar-row {
        grid-template-columns: minmax(7rem, 1fr) minmax(6rem, 2fr);
    }
    .detail-bar-share {
        display: none;
    }
}
@media (max-width: 600px) {
    .detail-pair-grid,
    .detail-finance-grid {
        grid-template-columns: 1fr;
    }
    .detail-location-record-fields {
        grid-template-columns: 1fr;
    }
    .detail-bar-row {
        grid-template-columns: 1fr;
    }
    .detail-bar-value {
        text-align: left;
    }
}
</style>
"""

VIEW_LABELS = {
    "gold.vw_project_detail_current": "identificação",
    "gold.vw_project_participant_current": "participantes",
    "gold.vw_project_location_current": "localização",
    "gold.vw_project_investment_current": "investimento previsto",
    "gold.vw_project_axis_type_current": "classificação da intervenção",
    "gold.vw_project_ppa_current": "PPA",
    "gold.vw_project_restriction_area_current": "áreas de restrição",
    "gold.vw_project_photo_indicator_current": "disponibilidade de foto",
    "gold.vw_project_contract_current": "contratos",
    "gold.vw_project_commitment_current": "empenhos",
    "gold.vw_project_commitment_totals_current": "totais financeiros",
    "gold.vw_project_execution_current": "execução física",
    "gold.vw_project_status_history_current": "histórico de situação",
    "gold.vw_project_feasibility_study_current": "estudos de viabilidade",
    "gold.vw_project_coverage_current": "cobertura do detalhe",
}

ROLE_LABELS = {
    "responsible": "Responsável",
    "transferor": "Repassador",
    "recipient": "Tomador",
    "executor": "Executor",
}

CONTRACT_LABELS = {
    "contract_source_id": "Contrato",
    "contract_number": "Número do contrato",
    "supplier_name": "Fornecedor",
    "supplier_cnpj": "CNPJ do fornecedor",
    "contract_status": "Situação do contrato",
    "validity_start_date": "Início da vigência",
    "validity_end_date": "Fim da vigência",
    "contract_object": "Objeto",
    "process_number": "Processo",
    "modality": "Modalidade",
    "organization_name": "Órgão contratante",
    "category": "Categoria",
    "procurement_number": "Número da contratação",
    "transparency_link": "Link de transparência",
    "valor_global_contrato": "Valor global",
    "valor_acumulado_contrato": "Valor acumulado",
    "valor_utilizado_pi_contrato": "Valor utilizado no projeto",
    "valor_incluido_contrato": "Valor incluído",
}

COMMITMENT_LABELS = {
    "commitment_key": "Identificador do registro",
    "commitment_number": "Número do empenho",
    "emission_date": "Data de emissão",
    "issuing_ug": "Unidade gestora emitente",
    "source_system": "Sistema de origem",
    "source_base": "Base de origem",
    "expense_nature": "Natureza da despesa",
    "creditor_name": "Credor",
    "commitment_description": "Descrição",
    "valor_empenho": "Empenhado",
    "aliquidar": "A liquidar",
    "liquidado": "Liquidado",
    "pago": "Pago",
    "rpinscrito": "Restos a pagar inscritos",
    "rpaliquidar": "Restos a pagar a liquidar",
    "rpaliquidado": "Restos a pagar liquidados",
    "rppago": "Restos a pagar pagos",
}


def _render_styles() -> None:
    st.markdown(DETAIL_CSS, unsafe_allow_html=True)


def _is_missing(value: object) -> bool:
    if value is None or value is pd.NA:
        return True
    if isinstance(value, list | tuple | set | dict):
        return False
    try:
        missing = pd.isna(value)
    except (TypeError, ValueError):
        return False
    return (
        bool(missing) if isinstance(missing, bool) or type(missing).__name__ == "bool_" else False
    )


def _display(value: object) -> str:
    if _is_missing(value):
        return "Não informado pela fonte"
    if isinstance(value, list | tuple | set):
        return ", ".join(_display(item) for item in value)
    if isinstance(value, Mapping):
        return "; ".join(f"{key}: {_display(item)}" for key, item in value.items())
    text = str(value).strip()
    return text or "Não informado pela fonte"


def _escape(value: object) -> str:
    return html.escape(_display(value))


def _format_date(value: object, *, include_time: bool = False) -> str:
    if _is_missing(value):
        return "Não informado pela fonte"
    parsed = pd.to_datetime(value, errors="coerce")
    if _is_missing(parsed):
        return _display(value)
    return parsed.strftime("%d/%m/%Y %H:%M" if include_time else "%d/%m/%Y")


def _format_datetime(value: object) -> str:
    return _format_date(value, include_time=True)


def _format_number(value: float, decimals: int = 2) -> str:
    formatted = f"{value:,.{decimals}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def _format_currency(value: object, *, compact: bool = False) -> str:
    if _is_missing(value):
        return "Não informado pela fonte"
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return _display(value)
    if not math.isfinite(amount):
        return "Não informado pela fonte"
    if compact:
        absolute = abs(amount)
        for divisor, suffix in ((1_000_000_000, "bi"), (1_000_000, "mi"), (1_000, "mil")):
            if absolute >= divisor:
                sign = "-" if amount < 0 else ""
                return f"R$ {sign}{_format_number(absolute / divisor, 1)} {suffix}"
    return f"R$ {_format_number(amount)}"


def _format_percent(value: object) -> str:
    if _is_missing(value):
        return "Não informado pela fonte"
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return _display(value)
    if not math.isfinite(amount):
        return "Não informado pela fonte"
    return f"{_format_number(amount, 0)}%"


def _frame(data: gold.ProjectDetailData, view_name: str) -> pd.DataFrame:
    columns = gold.DETAIL_VIEW_COLUMNS[view_name]
    return data.sections.get(view_name, pd.DataFrame(columns=columns)).reindex(
        columns=list(columns), fill_value=pd.NA
    )


def _unique_values(frame: pd.DataFrame, column: str) -> list[str]:
    if column not in frame.columns:
        return []
    values: list[str] = []
    for value in frame[column].tolist():
        text = _display(value)
        if text != "Não informado pela fonte" and text not in values:
            values.append(text)
    return values


def _join_values(frame: pd.DataFrame, column: str) -> str:
    values = _unique_values(frame, column)
    return ", ".join(values) if values else "Não informado pela fonte"


def _location_label(location: pd.DataFrame) -> str:
    values = []
    for _, row in location.iterrows():
        municipality = _display(row.get("municipality_name"))
        if municipality == "Não informado pela fonte":
            continue
        uf = _display(row.get("uf"))
        label = municipality if uf == "Não informado pela fonte" else f"{municipality} — {uf}"
        if label not in values:
            values.append(label)
    if values:
        return ", ".join(values)
    has_pin = any(
        _display(row.get("pin_name")) != "Não informado pela fonte"
        for _, row in location.iterrows()
    )
    return "Ponto de referência informado pela fonte" if has_pin else "Não informado pela fonte"


def _period_label(header: pd.DataFrame) -> str:
    if header.empty:
        return "Não informado pela fonte"
    row = header.iloc[0]
    start = _format_date(row.get("expected_start_date"))
    end = _format_date(row.get("expected_end_date"))
    return f"{start} — {end}"


def _coverage_label(coverage: pd.DataFrame) -> str:
    if coverage.empty or "has_data" not in coverage.columns:
        return "Não informado pela fonte"
    available = 0
    for value in coverage["has_data"].tolist():
        if isinstance(value, bool) and value:
            available += 1
        elif str(value).strip().casefold() in {"true", "t", "1", "sim"}:
            available += 1
    return f"{available} de {len(coverage)} blocos"


def _section_heading(title: str, note: str | None = None) -> None:
    note_html = f'<span class="detail-section-note">{html.escape(note)}</span>' if note else ""
    st.markdown(
        f'<div class="detail-section-heading"><h2>{html.escape(title)}</h2>{note_html}</div>',
        unsafe_allow_html=True,
    )


def _pair_grid(pairs: list[tuple[str, object]]) -> None:
    items = []
    for label, value in pairs:
        items.append(
            '<div class="detail-pair">'
            f'<span class="detail-pair-label">{html.escape(label)}</span>'
            f'<span class="detail-pair-value">{_escape(value)}</span>'
            "</div>"
        )
    st.markdown(f'<div class="detail-pair-grid">{"".join(items)}</div>', unsafe_allow_html=True)


def _display_frame(
    frame: pd.DataFrame,
    columns: tuple[str, ...],
    labels: Mapping[str, str],
    formats: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    result = frame.reindex(columns=list(columns), fill_value=pd.NA).copy()
    formats = formats or {}
    for column, format_name in formats.items():
        if column not in result.columns:
            continue
        if format_name == "currency":
            result[column] = result[column].map(_format_currency)
        elif format_name == "date":
            result[column] = result[column].map(_format_date)
        elif format_name == "datetime":
            result[column] = result[column].map(_format_datetime)
        elif format_name == "percent":
            result[column] = result[column].map(_format_percent)
    for column in result.columns:
        result[column] = result[column].map(_display)
    return result.rename(columns=dict(labels))


def _render_selector() -> None:
    _section_heading("Abrir um projeto", "Consulta direta pelo identificador público")
    try:
        overview = gold.load_overview_data()
    except gold.GoldError as error:
        st.error("Não foi possível carregar a lista de projetos atuais.")
        if error.ingestion_id is not None:
            st.caption(f"Código de referência: {_display(error.ingestion_id)}")
        return

    market = overview.market_overview
    if market.empty:
        st.info("Nenhum projeto está disponível no recorte atual.")
        return
    options = [str(value) for value in market["project_id"].dropna().tolist()]
    labels = {
        str(row.project_id): f"{_display(row.project_name)} · {row.project_id}"
        for row in market.itertuples()
    }
    selected = st.selectbox(
        "Projeto",
        options,
        format_func=lambda value: labels.get(value, value),
        key="detail_project_selector",
    )
    if st.button("Abrir detalhe", type="primary", key="open_detail"):
        st.query_params["project_id"] = selected
        st.rerun()


def _render_header(header: pd.DataFrame, location: pd.DataFrame) -> None:
    row = header.iloc[0]
    st.page_link("pages/overview.py", label="← Voltar à visão geral")
    title_column, snapshot_column = st.columns([5, 2])
    with title_column:
        title = _escape(row.get("project_name"))
        status = _escape(row.get("source_status"))
        organization = _escape(row.get("organization_name"))
        project_id = _escape(row.get("project_id"))
        location_text = _escape(_location_label(location))
        st.markdown(
            f'<div class="detail-title-row"><h1 class="detail-title">{title}</h1></div>'
            '<div class="detail-badge-row">'
            '<span class="detail-title-chip">Registro oficial</span>'
            f'<span class="detail-status-chip">{status}</span></div>'
            f'<div class="detail-meta">ID do projeto: {project_id}'
            f'<span class="detail-meta-dot">•</span>Órgão responsável: {organization}'
            f'<span class="detail-meta-dot">•</span>Localização: {location_text}</div>',
            unsafe_allow_html=True,
        )
    with snapshot_column:
        st.markdown(
            '<div class="detail-snapshot"><strong>Dados atualizados</strong>'
            f"<br>Data de referência: {_escape(_format_datetime(row.get('source_updated_at')))}"
            f"<br>Atualizado no painel: {_escape(_format_datetime(row.get('ingested_at')))}</div>",
            unsafe_allow_html=True,
        )


def _render_kpis(header: pd.DataFrame, coverage: pd.DataFrame) -> None:
    row = header.iloc[0]
    metrics = (
        (
            "R$",
            "Investimento previsto",
            _format_currency(row.get("planned_investment_amount")),
            "Valor total previsto para o projeto.",
        ),
        ("◷", "Período previsto", _period_label(header), "Datas previstas informadas pela fonte."),
        (
            "▦",
            "Cobertura do detalhe",
            _coverage_label(coverage),
            "Blocos com registros disponíveis para este projeto.",
        ),
    )
    columns = st.columns(3, gap="medium")
    for column, (icon, label, value, help_text) in zip(columns, metrics, strict=True):
        with column:
            st.markdown(
                f'<div class="detail-kpi-card" title="{html.escape(help_text)}">'
                f'<div class="detail-kpi-icon">{html.escape(icon)}</div>'
                f'<div class="detail-kpi-label">{html.escape(label)}</div>'
                f'<div class="detail-kpi-value">{html.escape(value)}</div></div>',
                unsafe_allow_html=True,
            )


def _render_location(location: pd.DataFrame) -> None:
    _section_heading("Localização", "Municípios e coordenadas informados pela fonte")
    if location.empty:
        st.info("Não há localização informada pela fonte.")
        return
    map_data = location[["latitude", "longitude"]].copy()
    map_data["latitude"] = pd.to_numeric(map_data["latitude"], errors="coerce")
    map_data["longitude"] = pd.to_numeric(map_data["longitude"], errors="coerce")
    map_data = map_data.dropna(subset=["latitude", "longitude"])
    map_height = min(500, max(360, 250 + len(location) * 110))
    map_column, list_column = st.columns([1.12, 1], gap="medium")
    with map_column:
        if map_data.empty:
            st.info("A fonte não informou coordenadas para este projeto.")
        else:
            with st.container(key="detail_location_map"):
                st.map(
                    map_data,
                    latitude="latitude",
                    longitude="longitude",
                    use_container_width=True,
                    height=map_height,
                )
                missing_coordinates = len(location) - len(map_data)
                if missing_coordinates == 1:
                    coordinate_note = " 1 registro sem coordenada permanece na lista."
                elif missing_coordinates > 1:
                    coordinate_note = (
                        f" {missing_coordinates} registros sem coordenada permanecem na lista."
                    )
                else:
                    coordinate_note = ""
                help_text = (
                    "O mapa mostra somente pontos com latitude e longitude informadas pela "
                    "fonte. Municípios, geometrias e pontos sem coordenadas permanecem na "
                    f"lista ao lado.{coordinate_note}"
                )
                st.markdown(
                    '<div class="detail-map-help-anchor">'
                    '<div class="detail-map-help">'
                    '<span class="detail-map-help-icon" role="img" tabindex="0" '
                    'aria-label="Informações do mapa">i</span>'
                    f'<div class="detail-map-help-tooltip" role="tooltip">'
                    f"{html.escape(help_text)}</div>"
                    "</div></div>",
                    unsafe_allow_html=True,
                )
    with list_column:
        st.markdown(
            '<div class="detail-location-summary">'
            f'<div class="detail-location-stat"><strong>{len(location)}</strong>'
            "<span>registros territoriais</span></div>"
            f'<div class="detail-location-stat"><strong>{len(map_data)}</strong>'
            "<span>com coordenadas no mapa</span></div></div>",
            unsafe_allow_html=True,
        )
        records = []
        for _, row in location.iterrows():
            location_type = (
                "Município"
                if _display(row.get("municipality_name")) != "Não informado pela fonte"
                else "Ponto de referência"
            )
            municipality = _display(row.get("municipality_name"))
            uf = _display(row.get("uf"))
            municipality_label = (
                municipality if uf == "Não informado pela fonte" else f"{municipality} — {uf}"
            )
            coordinates = (
                f"{_display(row.get('latitude'))}, {_display(row.get('longitude'))}"
                if not _is_missing(row.get("latitude")) and not _is_missing(row.get("longitude"))
                else "Não informado pela fonte"
            )
            fields = (
                ("Município / UF", municipality_label),
                ("Código IBGE", row.get("ibge_code")),
                ("ID da geometria", row.get("geometry_id")),
                ("Origem da localização", row.get("geometry_origin")),
                ("Ponto de referência", row.get("pin_name")),
                ("Coordenadas", coordinates),
            )
            field_html = "".join(
                '<div><span class="detail-location-field-label">'
                f'{html.escape(label)}</span><span class="detail-location-field-value">'
                f"{_escape(value)}</span></div>"
                for label, value in fields
            )
            records.append(
                '<article class="detail-location-record">'
                f'<div class="detail-location-record-title">{html.escape(location_type)}'
                f'</div><div class="detail-location-record-fields">{field_html}</div></article>'
            )
        st.markdown(
            f'<div class="detail-location-list">{"".join(records)}</div>',
            unsafe_allow_html=True,
        )
        if len(map_data) < len(location):
            st.caption("Localizações sem coordenadas permanecem listadas.")


def _render_identification(header: pd.DataFrame, axis: pd.DataFrame) -> None:
    _section_heading("Identificação e intervenção")
    row = header.iloc[0]
    _pair_grid(
        [
            ("Órgão responsável", row.get("organization_name")),
            ("CNPJ do órgão", row.get("organization_cnpj")),
            ("UF principal", row.get("uf_principal")),
            ("Natureza da intervenção", row.get("nature_intervention")),
            ("Espécie da intervenção", row.get("species_intervention")),
            ("Eixo", _join_values(axis, "axis_name")),
            ("Tipo", _join_values(axis, "type_name")),
            ("Subtipo", _join_values(axis, "subtype_name")),
            ("População beneficiada", row.get("benefited_population")),
            ("Projeto BIM", row.get("bim_indicator")),
            ("Ano de cadastro", row.get("registration_year")),
            ("Data prevista de início", _format_date(row.get("expected_start_date"))),
            ("Data prevista de conclusão", _format_date(row.get("expected_end_date"))),
        ]
    )


def _render_participants(frame: pd.DataFrame) -> None:
    _section_heading("Órgãos e participantes", "Papéis preservados conforme o registro oficial")
    if frame.empty:
        st.info("Não há participantes informados pela fonte.")
        return
    roles = _unique_values(frame, "participant_role")
    tabs = st.tabs([ROLE_LABELS.get(role, role) for role in roles])
    for tab, role in zip(tabs, roles, strict=True):
        with tab:
            subset = frame[frame["participant_role"].map(_display) == role]
            st.dataframe(
                _display_frame(
                    subset,
                    ("organization_name", "organization_cnpj", "source_participant_count"),
                    {
                        "organization_name": "Organização",
                        "organization_cnpj": "CNPJ",
                        "source_participant_count": "Registros de origem",
                    },
                ),
                hide_index=True,
                use_container_width=True,
            )


def _render_context(
    header: pd.DataFrame,
    axis: pd.DataFrame,
    ppa: pd.DataFrame,
    restrictions: pd.DataFrame,
    photos: pd.DataFrame,
) -> None:
    _section_heading("Contexto da intervenção")
    row = header.iloc[0]
    description = _display(row.get("description"))
    if description != "Não informado pela fonte":
        st.markdown(
            f'<div class="detail-prose">{_escape(description)}</div>', unsafe_allow_html=True
        )
    _pair_grid(
        [
            ("Função social", row.get("social_function_description")),
            ("Meta global", row.get("global_goal_description")),
            ("Descrição da população", row.get("benefited_population_description")),
            ("Empregos gerados", row.get("jobs_created_count")),
            ("Projeto estruturante", row.get("structural_project_indicator")),
            ("Sistema responsável", row.get("source_system")),
            ("Endereço", row.get("address_description")),
            ("CEP", row.get("postal_code")),
            ("Observações", row.get("intervention_notes")),
            ("Disponibilidade de foto", _join_values(photos, "ind_foto")),
        ]
    )
    st.markdown("**Planejamento plurianual**")
    if ppa.empty:
        st.info("Não informado pela fonte.")
    else:
        st.dataframe(
            _display_frame(
                ppa,
                ("ppa_type", "ppa_description"),
                {"ppa_type": "Tipo", "ppa_description": "Descrição"},
            ),
            hide_index=True,
            use_container_width=True,
        )
    st.markdown("**Áreas de restrição declaradas pela fonte**")
    if restrictions.empty:
        st.info("Não informado pela fonte.")
    else:
        st.dataframe(
            _display_frame(
                restrictions,
                ("restriction_area",),
                {"restriction_area": "Área"},
            ),
            hide_index=True,
            use_container_width=True,
        )


def _render_dates(header: pd.DataFrame) -> None:
    _section_heading("Marcos do projeto", "Datas previstas e efetivas, sem cálculo de prazo")
    row = header.iloc[0]
    _pair_grid(
        [
            ("Cadastro", _format_date(row.get("registration_date"))),
            ("Início previsto", _format_date(row.get("expected_start_date"))),
            ("Conclusão prevista", _format_date(row.get("expected_end_date"))),
            ("Início efetivo", _format_date(row.get("actual_start_date"))),
            ("Conclusão efetiva", _format_date(row.get("actual_end_date"))),
        ]
    )


def _render_investment(frame: pd.DataFrame, total_value: object) -> None:
    _section_heading("Investimento por fonte", "Apenas investimento previsto")
    total = float(total_value) if not _is_missing(total_value) else math.nan
    if frame.empty:
        st.info("Não há abertura do investimento por fonte.")
        return
    amounts = pd.to_numeric(frame["planned_investment_amount"], errors="coerce")
    chart = frame.copy()
    chart["amount"] = amounts
    chart = chart.dropna(subset=["amount"])
    if not math.isfinite(total):
        total = float(chart["amount"].sum()) if not chart.empty else math.nan
    bar_column, total_column = st.columns([5, 1.2], gap="large")
    with bar_column:
        if chart.empty:
            st.info("Não há valores de investimento informados pela fonte.")
        else:
            for _, row in chart.iterrows():
                amount = float(row["amount"])
                share = amount / total * 100 if math.isfinite(total) and total > 0 else 0
                width = min(max(share, 0), 100)
                source_label = _escape(row.get("funding_source_name"))
                bar_fill = (
                    '<div class="detail-bar-track">'
                    f'<div class="detail-bar-fill" style="width:{width:.2f}%"></div></div>'
                )
                amount_label = html.escape(_format_currency(amount, compact=True))
                st.markdown(
                    '<div class="detail-bar-row">'
                    f'<span class="detail-bar-label">{source_label}</span>'
                    f"{bar_fill}"
                    f'<span class="detail-bar-value">{amount_label}</span>'
                    f'<span class="detail-bar-share">{share:.1f}%</span></div>',
                    unsafe_allow_html=True,
                )
    with total_column:
        total_text = (
            _format_currency(total, compact=True)
            if math.isfinite(total)
            else "Não informado pela fonte"
        )
        st.markdown(
            '<div class="detail-total-card"><div class="detail-total-label">Total previsto</div>'
            f'<div class="detail-total-value">{html.escape(total_text)}</div>'
            '<div class="detail-total-label">Abertura por fonte</div></div>',
            unsafe_allow_html=True,
        )


def _render_execution(frame: pd.DataFrame) -> None:
    _section_heading("Execução física", "Registros distintos informados pela fonte")
    if frame.empty:
        st.info("Não há registro de execução física informado pela fonte.")
        return
    columns = (
        "instrument",
        "execution_registration_at",
        "execution_start_date",
        "execution_end_date",
        "instrument_creation_date",
        "source_update_date",
        "execution_form",
        "indicators",
        "reasons",
        "source_record_count",
    )
    labels = {
        "instrument": "Instrumento",
        "execution_registration_at": "Registro",
        "execution_start_date": "Início",
        "execution_end_date": "Conclusão",
        "instrument_creation_date": "Criação do instrumento",
        "source_update_date": "Atualização",
        "execution_form": "Forma de execução",
        "indicators": "Indicadores",
        "reasons": "Motivos",
        "source_record_count": "Registros de origem",
    }
    formats = {
        "execution_registration_at": "datetime",
        "execution_start_date": "date",
        "execution_end_date": "date",
        "instrument_creation_date": "date",
        "source_update_date": "date",
    }
    for index, (_, row) in enumerate(frame.iterrows(), start=1):
        identifier = _escape(row.get("id_execucao_fisica"))
        with st.container(border=True, key=f"detail_execution_record_{index}"):
            st.markdown(
                '<span class="detail-execution-record-marker"></span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="detail-record-title">Registro {identifier} · '
                f"{_escape(row.get('instrument'))}</div>",
                unsafe_allow_html=True,
            )
            metric_column, detail_column = st.columns([1.25, 2.75], gap="small")
            with metric_column:
                percent_label = _format_percent(row.get("physical_execution_percentage"))
                st.markdown(
                    '<div class="detail-total-card detail-execution-percent-card">'
                    '<div class="detail-total-label">Percentual informado</div>'
                    f'<div class="detail-total-value">{html.escape(percent_label)}</div></div>',
                    unsafe_allow_html=True,
                )
            with detail_column:
                st.dataframe(
                    _display_frame(pd.DataFrame([row]), columns, labels, formats),
                    hide_index=True,
                    use_container_width=True,
                )


def _render_contracts(frame: pd.DataFrame) -> None:
    _section_heading(
        "Contratos e fornecedores",
        "Valores contratuais mantidos separados do investimento previsto",
    )
    if frame.empty:
        st.info("Não há contratos informados pela fonte.")
        return
    st.markdown(
        f'<span class="detail-count-chip">{len(frame)} contratos distintos</span>',
        unsafe_allow_html=True,
    )
    summary_columns = (
        "contract_number",
        "supplier_name",
        "contract_status",
        "contract_object",
        "valor_global_contrato",
        "validity_start_date",
        "validity_end_date",
    )
    summary_labels = {
        "contract_number": "Número do contrato",
        "supplier_name": "Fornecedor",
        "contract_status": "Situação",
        "contract_object": "Objeto",
        "valor_global_contrato": "Valor global",
        "validity_start_date": "Início",
        "validity_end_date": "Fim",
    }
    st.dataframe(
        _display_frame(
            frame,
            summary_columns,
            summary_labels,
            {
                "valor_global_contrato": "currency",
                "validity_start_date": "date",
                "validity_end_date": "date",
            },
        ),
        hide_index=True,
        use_container_width=True,
    )
    for index, (_, row) in enumerate(frame.reset_index(drop=True).iterrows()):
        identifier = _display(row.get("contract_source_id"))
        with st.expander(f"Detalhes do contrato {identifier}", expanded=index == 0):
            columns = tuple(column for column in CONTRACT_LABELS if column in row.index)
            formats = {column: "currency" for column in columns if column.startswith("valor_")}
            formats.update({column: "date" for column in columns if column.endswith("_date")})
            st.dataframe(
                _display_frame(row.to_frame().T, columns, CONTRACT_LABELS, formats),
                hide_index=True,
                use_container_width=True,
            )
            link = row.get("transparency_link")
            if isinstance(link, str) and urlparse(link).scheme in {"http", "https"}:
                st.link_button("Abrir transparência", link)


def _finance_items(values: Mapping[str, object], labels: Mapping[str, str]) -> None:
    items = []
    for column, label in labels.items():
        value = html.escape(_format_currency(values.get(column)))
        items.append(
            '<div class="detail-finance-item">'
            f'<span class="detail-finance-item-label">{html.escape(label)}</span>'
            f'<span class="detail-finance-item-value">{value}</span>'
            "</div>"
        )
    st.markdown(f'<div class="detail-finance-grid">{"".join(items)}</div>', unsafe_allow_html=True)


def _render_commitments(frame: pd.DataFrame, totals: pd.DataFrame) -> None:
    _section_heading(
        "Empenhos e execução financeira", "Grandezas financeiras apresentadas separadamente"
    )
    if totals.empty and frame.empty:
        st.info("Não há informações financeiras informadas pela fonte.")
        return
    summary = totals.iloc[0].to_dict() if not totals.empty else {}
    st.markdown(
        '<div class="detail-finance-group">'
        '<div class="detail-finance-label">Medidas do empenho</div>',
        unsafe_allow_html=True,
    )
    _finance_items(
        summary,
        {
            "valor_empenho": "Empenhado",
            "aliquidar": "A liquidar",
            "liquidado": "Liquidado",
            "pago": "Pago",
        },
    )
    st.markdown(
        '</div><div class="detail-finance-group">'
        '<div class="detail-finance-label">Restos a pagar</div>',
        unsafe_allow_html=True,
    )
    _finance_items(
        summary,
        {
            "rpinscrito": "Inscritos",
            "rpaliquidar": "A liquidar",
            "rpaliquidado": "Liquidados",
            "rppago": "Pagos",
        },
    )
    st.markdown("</div>", unsafe_allow_html=True)
    if not frame.empty:
        with st.expander(f"Ver empenhos individuais ({len(frame)})"):
            columns = tuple(column for column in COMMITMENT_LABELS if column in frame.columns)
            formats = {
                column: "currency" for column in columns if column.startswith(("valor_", "rp"))
            }
            formats["emission_date"] = "date"
            st.dataframe(
                _display_frame(frame, columns, COMMITMENT_LABELS, formats),
                hide_index=True,
                use_container_width=True,
            )


def _render_studies(frame: pd.DataFrame) -> None:
    _section_heading("Estudos de viabilidade")
    if frame.empty:
        st.info("Não há estudos de viabilidade informados pela fonte.")
        return
    st.markdown(
        f'<span class="detail-count-chip">{len(frame)} estudos associados</span> '
        '<span class="detail-partial-chip">Dados parciais</span>',
        unsafe_allow_html=True,
    )
    st.caption(
        "A fonte informa tipo e especificação; situação, data e conclusão não foram fornecidas."
    )
    st.dataframe(
        _display_frame(
            frame,
            ("study_type", "study_specification"),
            {"study_type": "Estudo", "study_specification": "Especificação"},
        ),
        hide_index=True,
        use_container_width=True,
    )


def _render_history(frame: pd.DataFrame) -> None:
    _section_heading(
        "Histórico de cancelamento e paralisação", "Somente situações recebidas neste recorte"
    )
    if frame.empty:
        st.info("Não há cancelamentos ou paralisações informados pela fonte.")
        return
    columns = (
        "event_date",
        "source_status",
        "justification",
        "treatment_indicator",
        "treatment_phase",
        "source_event_count",
        "source_event_ids",
    )
    labels = {
        "event_date": "Data",
        "source_status": "Situação",
        "justification": "Justificativa",
        "treatment_indicator": "Tratamento",
        "treatment_phase": "Fase",
        "source_event_count": "Registros de origem",
        "source_event_ids": "Identificadores de origem",
    }
    st.dataframe(
        _display_frame(frame.head(10), columns, labels, {"event_date": "date"}),
        hide_index=True,
        use_container_width=True,
    )
    if len(frame) > 10:
        with st.expander(f"Ver histórico completo ({len(frame)} registros semânticos)"):
            st.dataframe(
                _display_frame(frame, columns, labels, {"event_date": "date"}),
                hide_index=True,
                use_container_width=True,
            )


def _render_coverage(frame: pd.DataFrame, header: pd.DataFrame, studies: pd.DataFrame) -> None:
    with st.expander("Ver cobertura e rastreabilidade"):
        _section_heading("Cobertura do detalhe", "Disponibilidade dos blocos no registro atual")
        if not frame.empty:
            st.dataframe(
                _display_frame(
                    frame,
                    (
                        "section_name",
                        "source_record_count",
                        "display_record_count",
                        "coverage_status",
                    ),
                    {
                        "section_name": "Bloco",
                        "source_record_count": "Registros de origem",
                        "display_record_count": "Registros apresentados",
                        "coverage_status": "Cobertura",
                    },
                ),
                hide_index=True,
                use_container_width=True,
            )
        if not header.empty:
            indicator = _display(header.iloc[0].get("feasibility_study_indicator")).upper()
            observed = "SIM" if not studies.empty else "NÃO"
            if indicator not in {"NÃO INFORMADO PELA FONTE", observed}:
                st.warning(
                    "O indicador declarado para estudos diverge dos registros recebidos; "
                    "as duas informações foram preservadas."
                )


def _render_snapshot_footer(header: pd.DataFrame) -> None:
    row = header.iloc[0]
    st.markdown(
        '<div class="detail-footer">'
        f"Atualização da fonte: {_escape(_format_datetime(row.get('source_updated_at')))}"
        '<span class="detail-meta-dot">•</span>'
        f"Atualizado no painel: {_escape(_format_datetime(row.get('ingested_at')))}"
        '<span class="detail-meta-dot">•</span>'
        f"Código de referência: {_escape(row.get('ingestion_id'))}</div>",
        unsafe_allow_html=True,
    )


def _render_error(error: gold.GoldError) -> None:
    st.error("Não foi possível carregar o detalhe do projeto.")
    st.caption("Verifique a disponibilidade dos dados e tente novamente.")
    if error.ingestion_id is not None:
        st.caption(f"Código de referência: {_display(error.ingestion_id)}")
    if st.button("Tentar novamente", key="detail_retry"):
        st.cache_data.clear()
        st.rerun()


def _render_section_errors(errors: dict[str, gold.GoldError]) -> None:
    for view_name in errors:
        label = VIEW_LABELS.get(view_name, "bloco do detalhe")
        st.error(f"O bloco de {label} está indisponível. Os demais dados foram preservados.")


def _resolve_project_id() -> str | None:
    project_id = st.query_params.get("project_id")
    if project_id:
        st.session_state.pop(DETAIL_PROJECT_SESSION_KEY, None)
        return str(project_id)

    pending_project_id = st.session_state.pop(DETAIL_PROJECT_SESSION_KEY, None)
    if pending_project_id:
        project_id = str(pending_project_id).strip()
        if project_id:
            st.query_params["project_id"] = project_id
            return project_id
    return None


def main() -> None:
    _render_styles()
    project_id = _resolve_project_id()
    if not project_id:
        st.markdown('<h1 class="detail-title">Detalhe do projeto</h1>', unsafe_allow_html=True)
        st.info("Selecione um projeto na visão geral ou use o seletor abaixo.")
        with st.container(border=True):
            _render_selector()
        return

    try:
        data = gold.load_project_detail(str(project_id))
    except gold.GoldError as error:
        _render_error(error)
        return

    header = _frame(data, DETAIL_VIEW)
    if header.empty:
        st.page_link("pages/overview.py", label="← Voltar à visão geral")
        st.markdown('<h1 class="detail-title">Detalhe do projeto</h1>', unsafe_allow_html=True)
        st.info("O projeto informado não existe no registro atual ou está fora do recorte.")
        return

    location = _frame(data, "gold.vw_project_location_current")
    coverage = _frame(data, "gold.vw_project_coverage_current")
    axis = _frame(data, "gold.vw_project_axis_type_current")
    studies = _frame(data, "gold.vw_project_feasibility_study_current")

    _render_header(header, location)
    _render_kpis(header, coverage)

    location_column, identification_column = st.columns([1.05, 1], gap="medium")
    with location_column:
        with st.container(border=True):
            _render_location(location)
    with identification_column:
        with st.container(border=True):
            _render_identification(header, axis)

    with st.container(border=True):
        _render_participants(_frame(data, "gold.vw_project_participant_current"))

    with st.container(border=True):
        _render_context(
            header,
            axis,
            _frame(data, "gold.vw_project_ppa_current"),
            _frame(data, "gold.vw_project_restriction_area_current"),
            _frame(data, "gold.vw_project_photo_indicator_current"),
        )

    with st.container(border=True):
        _render_dates(header)

    with st.container(border=True):
        _render_investment(
            _frame(data, "gold.vw_project_investment_current"),
            header.iloc[0].get("planned_investment_amount"),
        )

    execution_column, contracts_column = st.columns([1, 1.25], gap="medium")
    with execution_column:
        with st.container(border=True):
            _render_execution(_frame(data, "gold.vw_project_execution_current"))
    with contracts_column:
        with st.container(border=True):
            _render_contracts(_frame(data, "gold.vw_project_contract_current"))

    with st.container(border=True):
        _render_commitments(
            _frame(data, "gold.vw_project_commitment_current"),
            _frame(data, "gold.vw_project_commitment_totals_current"),
        )

    studies_column, history_column = st.columns([1, 1], gap="medium")
    with studies_column:
        with st.container(border=True):
            _render_studies(studies)
    with history_column:
        with st.container(border=True):
            _render_history(_frame(data, "gold.vw_project_status_history_current"))

    _render_coverage(coverage, header, studies)
    _render_section_errors(data.errors)
    _render_snapshot_footer(header)


main()
