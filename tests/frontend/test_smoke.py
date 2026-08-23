from __future__ import annotations

import tomllib
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from frontend import gold

APP_PATH = Path(__file__).resolve().parents[2] / "frontend" / "streamlit_app.py"
FAVICON_PATH = Path(__file__).resolve().parents[2] / "assets" / "brand" / "vertere-ai-favicon.png"
DETAIL_PATH = Path(__file__).resolve().parents[2] / "frontend" / "pages" / "project_detail.py"
STREAMLIT_CONFIG_PATH = Path(__file__).resolve().parents[2] / ".streamlit" / "config.toml"


def test_disables_streamlit_automatic_sidebar_navigation() -> None:
    config = tomllib.loads(STREAMLIT_CONFIG_PATH.read_text(encoding="utf-8"))

    assert config["client"]["showSidebarNavigation"] is False


def _overview_data() -> gold.OverviewData:
    market = pd.DataFrame(
        {
            "project_id": ["p-1", "p-2"],
            "project_name": ["Obra Alfa", "Obra Beta"],
            "description": ["Descrição Alfa", None],
            "organization_name": ["Órgão A", "Órgão B"],
            "organization_cnpj": [None, "00.000.000/0001-00"],
            "source_status": ["Em execução", "Concluídas"],
            "uf_principal": ["CE", "CE"],
            "nature_intervention": ["Obra", "Obra"],
            "species_intervention": ["Construção", "Construção"],
            "axis_name": ["Infraestrutura", "Educação"],
            "type_name": ["Rodovia", "Escola"],
            "subtype_name": ["Pavimentação", "Edificação"],
            "registration_date": ["2026-01-10", "2026-02-12"],
            "registration_year": [2026, 2026],
            "expected_start_date": [None, None],
            "expected_end_date": [None, None],
            "planned_investment_amount": [1_500_000, 2_500_000],
            "municipality_names": ["Fortaleza", "Sobral"],
            "ibge_codes": ["2304400", "2312908"],
            "source_updated_at": ["2026-08-21T08:00:00Z"] * 2,
            "ingested_at": ["2026-08-21T08:30:00Z"] * 2,
            "ingestion_id": ["ing-1"] * 2,
        }
    )
    location = pd.DataFrame(
        {
            "project_id": ["p-1", "p-2"],
            "municipality_name": ["Fortaleza", "Sobral"],
            "ibge_code": ["2304400", "2312908"],
            "uf": ["CE", "CE"],
            "latitude": [-3.73, -3.68],
            "longitude": [-38.52, -40.35],
            "planned_investment_amount": [1_500_000, 2_500_000],
        }
    )
    status = pd.DataFrame(
        {
            "source_status": ["Concluídas", "Em execução"],
            "project_count": [1, 1],
        }
    )
    snapshot = pd.DataFrame(
        {
            "ingestion_id": ["ing-1"],
            "source_updated_at": ["2026-08-21T08:00:00Z"],
            "ingested_at": ["2026-08-21T08:30:00Z"],
            "project_count": [2],
            "planned_investment_amount": [4_000_000],
            "municipality_count": [2],
            "execution_project_count": [1],
        }
    )
    return gold.OverviewData(market, location, status, snapshot)


def _filtered_metrics_data() -> gold.FilteredMetrics:
    data = _overview_data()
    return gold.FilteredMetrics(
        kpis=data.snapshot_metadata[
            [
                "project_count",
                "planned_investment_amount",
                "municipality_count",
                "execution_project_count",
            ]
        ],
        status_distribution=data.status_distribution,
    )


def test_overview_app_smoke_without_database(monkeypatch: pytest.MonkeyPatch) -> None:
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(gold, "load_overview_data", lambda: _overview_data())
    monkeypatch.setattr(
        gold, "load_filtered_metrics", lambda *_args, **_kwargs: _filtered_metrics_data()
    )
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    assert not app.exception
    assert any("Obras Públicas — Ceará" in item.value for item in app.markdown)
    assert any("Dados atualizados" in item.value for item in app.markdown)
    assert not any("Snapshot atual" in item.value for item in app.markdown)
    assert len(app.metric) == 4
    assert {item.label for item in app.metric} == {
        "Total de obras",
        "Investimento previsto",
        "Municípios alcançados",
        "Obras em execução",
    }
    assert {item.label for item in app.multiselect} == {
        "Município",
        "Organização responsável",
        "Situação da obra",
        "Área de atuação",
        "Tipo de obra",
        "Detalhamento do tipo",
        "Faixa de investimento",
        "Ano de registro",
    }
    period_filters = [item for item in app.selectbox if item.label == "Período de registro"]
    assert len(period_filters) == 1
    assert period_filters[0].value == "Sem filtro"
    assert period_filters[0].options == [
        "Sem filtro",
        "Último mês",
        "Últimos 3 meses",
        "Últimos 6 meses",
        "Últimos 12 meses",
        "Ano corrente",
    ]


def test_overview_table_keeps_investment_numeric_for_sorting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from frontend.pages import overview

    captured: dict[str, object] = {}
    monkeypatch.setattr(overview.st, "subheader", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        overview.st,
        "dataframe",
        lambda frame, **kwargs: (
            captured.update({"frame": frame, "kwargs": kwargs})
            or SimpleNamespace(selection=SimpleNamespace(rows=[]))
        ),
    )

    overview._render_table(_overview_data().market_overview)

    table_styler = captured["frame"]
    table = table_styler.data
    assert isinstance(table_styler, pd.io.formats.style.Styler)
    assert isinstance(table, pd.DataFrame)
    assert pd.api.types.is_numeric_dtype(table["Investimento previsto"])
    investment_config = captured["kwargs"]["column_config"]["Investimento previsto"]
    assert investment_config["type_config"]["type"] == "number"


def test_snapshot_card_hides_ingestion_id(monkeypatch: pytest.MonkeyPatch) -> None:
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(gold, "load_overview_data", lambda: _overview_data())
    monkeypatch.setattr(
        gold, "load_filtered_metrics", lambda *_args, **_kwargs: _filtered_metrics_data()
    )
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    assert not app.exception
    assert not any("ID:" in item.value for item in app.markdown)


def test_count_kpis_are_rendered_as_integers() -> None:
    from frontend.pages.overview import _format_count

    assert _format_count(3_205.0) == "3.205"
    assert _format_count(193.0) == "193"
    assert _format_count(695.0) == "695"


def test_streamlit_uses_the_compact_vertere_favicon() -> None:
    source = APP_PATH.read_text(encoding="utf-8")

    assert FAVICON_PATH.exists()
    assert "page_icon=str(FAVICON_PATH)" in source


def test_overview_map_exposes_instructions_in_hover_help(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(gold, "load_overview_data", lambda: _overview_data())
    monkeypatch.setattr(
        gold, "load_filtered_metrics", lambda *_args, **_kwargs: _filtered_metrics_data()
    )
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    assert not app.exception
    map_help = [
        item.value for item in app.markdown if '<div class="map-help-anchor">' in item.value
    ]
    assert len(map_help) == 1
    assert 'aria-label="Informações do mapa"' in map_help[0]
    assert "O mapa exibe os pontos com coordenadas informadas pela fonte" in map_help[0]
    assert (
        "As demais associações de localização permanecem disponíveis na lista de obras"
        in map_help[0]
    )
    assert "Cada ponto representa um município" not in map_help[0]
    assert "section-caption" not in map_help[0]


def test_overview_styles_include_dark_theme_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(gold, "load_overview_data", lambda: _overview_data())
    monkeypatch.setattr(
        gold, "load_filtered_metrics", lambda *_args, **_kwargs: _filtered_metrics_data()
    )
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    styles = "\n".join(item.value for item in app.markdown)
    assert "--vertere-ink: currentColor" in styles
    assert "--vertere-muted: color-mix" in styles
    assert "background: transparent" in styles
    assert "color: inherit" in styles
    assert ".snapshot-chip" in styles
    assert "margin-top: 0.75rem" in styles
    assert "margin-bottom: 0.75rem" in styles
    assert '[data-testid="stHeader"]' in styles
    assert "background: Canvas !important" in styles
    assert '[data-testid="stDeckGlJsonChart"] .mapboxgl-ctrl-attrib {' in styles
    assert '[data-testid="stVerticalBlock"]:has(.map-help-anchor)' in styles
    assert "bottom: 1.25rem" in styles


def test_status_chart_does_not_force_a_light_background(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from frontend.pages import overview

    captured: dict[str, object] = {}
    monkeypatch.setattr(overview.st, "subheader", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(overview.st, "caption", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        overview.st,
        "plotly_chart",
        lambda figure, **_kwargs: captured.__setitem__("figure", figure),
    )

    overview._render_status(pd.DataFrame({"source_status": ["Em execução"], "project_count": [3]}))

    figure = captured["figure"]
    assert figure.layout.plot_bgcolor == "rgba(0,0,0,0)"
    assert figure.layout.paper_bgcolor == "rgba(0,0,0,0)"


def test_overview_empty_state_without_database(monkeypatch: pytest.MonkeyPatch) -> None:
    from streamlit.testing.v1 import AppTest

    empty = gold.OverviewData(
        market_overview=pd.DataFrame(),
        project_location=pd.DataFrame(),
        status_distribution=pd.DataFrame(),
        snapshot_metadata=pd.DataFrame(
            {
                "ingestion_id": ["ing-empty"],
                "source_updated_at": [None],
                "ingested_at": [None],
            }
        ),
    )
    monkeypatch.setattr(gold, "load_overview_data", lambda: empty)
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    assert not app.exception
    assert any("Nenhuma obra corresponde" in item.value for item in app.info)


def test_overview_error_state_without_database(monkeypatch: pytest.MonkeyPatch) -> None:
    from streamlit.testing.v1 import AppTest

    def raise_error() -> gold.OverviewData:
        raise gold.GoldQueryError("erro simulado de teste", ingestion_id="ing-error")

    monkeypatch.setattr(gold, "load_overview_data", raise_error)
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    assert not app.exception
    assert any("Não foi possível carregar" in item.value for item in app.error)
    assert any("ing-error" in item.value for item in app.caption)


def test_overview_partial_state_preserves_missing_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    partial = _overview_data()
    partial.market_overview["planned_investment_amount"] = pd.Series(
        [pd.NA] * len(partial.market_overview),
        index=partial.market_overview.index,
        dtype="Float64",
    )
    partial.project_location.loc[0, ["latitude", "longitude"]] = None
    monkeypatch.setattr(gold, "load_overview_data", lambda: partial)
    monkeypatch.setattr(
        gold, "load_filtered_metrics", lambda *_args, **_kwargs: _filtered_metrics_data()
    )

    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    assert not app.exception
    partial_badge = [item.value for item in app.markdown if "Dados parciais" in item.value]
    assert len(partial_badge) == 1
    assert 'class="partial-tooltip"' in partial_badge[0]
    assert 'aria-describedby="partial-state-tooltip"' in partial_badge[0]
    assert "localiza" in partial_badge[0]
    assert not any("localiza" in str(item.value).lower() for item in app.caption)
    display_values = bytes(app.dataframe[0].proto.styler.display_values).decode(
        "utf-8",
        errors="ignore",
    )
    assert "Não informado" in display_values


def test_project_detail_without_project_id_offers_selector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(gold, "load_overview_data", lambda: _overview_data())
    app = AppTest.from_file(str(DETAIL_PATH), default_timeout=10).run()

    assert not app.exception
    assert any("seletor" in item.value.lower() for item in app.info)
    assert len(app.selectbox) == 1


def test_overview_selection_preserves_project_for_detail_navigation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from frontend.pages import overview

    query_params: dict[str, str] = {}
    session_state: dict[str, str] = {}
    switched_pages: list[str] = []
    event = SimpleNamespace(selection=SimpleNamespace(rows=[1]))

    monkeypatch.setattr(overview.st, "query_params", query_params)
    monkeypatch.setattr(overview.st, "session_state", session_state)
    monkeypatch.setattr(overview.st, "dataframe", lambda *_args, **_kwargs: event)
    monkeypatch.setattr(
        overview.st,
        "switch_page",
        lambda page: switched_pages.append(str(page)),
    )

    overview._render_table(_overview_data().market_overview)

    assert switched_pages == ["pages/project_detail.py"]
    assert query_params == {}
    assert session_state[overview.DETAIL_PROJECT_SESSION_KEY] == "p-2"


def test_project_detail_consumes_pending_project_after_switch_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import streamlit as st
    from streamlit.testing.v1 import AppTest

    detail_view = "gold.vw_project_detail_current"

    def load_detail(project_id: str) -> gold.ProjectDetailData:
        return gold.ProjectDetailData(
            project_id=project_id,
            sections={
                detail_view: pd.DataFrame(
                    {"project_id": [project_id], "project_name": ["Obra Beta"]}
                )
            },
        )

    monkeypatch.setattr(gold, "load_project_detail", load_detail)
    monkeypatch.setattr(st, "page_link", lambda *_args, **_kwargs: None)
    app = AppTest.from_file(str(DETAIL_PATH), default_timeout=10)
    app.session_state["_vertere_detail_project_id"] = "p-2"
    app.run()

    assert not app.exception
    assert app.query_params == {"project_id": ["p-2"]}
    assert any("Obra Beta" in item.value for item in app.markdown)
    assert "_vertere_detail_project_id" not in app.session_state


def test_project_detail_gold_loader_is_project_scoped(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeConnection:
        def query(self, query: str, **kwargs: object) -> pd.DataFrame:
            calls.append((query, kwargs.get("params", {})))
            if "vw_project_detail_current" in query:
                return pd.DataFrame(
                    {
                        "project_id": ["p-1"],
                        "project_name": ["Obra Alfa"],
                        "planned_investment_amount": [100],
                    }
                )
            return pd.DataFrame()

    monkeypatch.setenv("GOLD_DATABASE_URL", "postgresql+psycopg://test-only")
    monkeypatch.setattr(gold, "_connection", lambda: FakeConnection())
    gold.load_project_detail.clear()
    result = gold.load_project_detail("p-1")

    assert result.project_id == "p-1"
    assert len(calls) == len(gold.DETAIL_VIEW_COLUMNS)
    assert all("gold.vw_" in query and "_current" in query for query, _ in calls)
    assert all("bronze." not in query and "silver." not in query for query, _ in calls)
    assert all(params == {"project_id": "p-1"} for _, params in calls)


def test_project_detail_invalid_id_does_not_query_collections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeConnection:
        def query(self, query: str, **_: object) -> pd.DataFrame:
            calls.append(query)
            return pd.DataFrame(columns=gold.DETAIL_VIEW_COLUMNS["gold.vw_project_detail_current"])

    monkeypatch.setenv("GOLD_DATABASE_URL", "postgresql+psycopg://test-only")
    monkeypatch.setattr(gold, "_connection", lambda: FakeConnection())
    gold.load_project_detail.clear()
    result = gold.load_project_detail("does-not-exist")

    assert result.sections["gold.vw_project_detail_current"].empty
    assert len(calls) == 1
    assert "vw_project_detail_current" in calls[0]


def test_project_detail_preserves_other_sections_when_one_collection_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeConnection:
        def query(self, query: str, **_: object) -> pd.DataFrame:
            if "vw_project_contract_current" in query:
                raise RuntimeError("db indisponível")
            if "vw_project_detail_current" in query:
                return pd.DataFrame(
                    {
                        "project_id": ["p-1"],
                        "project_name": ["Obra Alfa"],
                        "planned_investment_amount": [100],
                    }
                )
            return pd.DataFrame()

    monkeypatch.setenv("GOLD_DATABASE_URL", "postgresql+psycopg://test-only")
    monkeypatch.setattr(gold, "_connection", lambda: FakeConnection())
    gold.load_project_detail.clear()
    result = gold.load_project_detail("p-1")

    assert "gold.vw_project_contract_current" in result.errors
    assert result.sections["gold.vw_project_contract_current"].empty
    assert result.sections["gold.vw_project_commitment_current"].empty


def test_gold_loader_queries_only_current_views(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class FakeConnection:
        def query(self, query: str, **_: object) -> pd.DataFrame:
            calls.append(query)
            if "vw_snapshot_metadata_current" in query:
                return pd.DataFrame(
                    {
                        "ingestion_id": ["ing-1"],
                        "source_updated_at": ["2026-08-21"],
                        "ingested_at": ["2026-08-21"],
                        "project_count": [2],
                        "planned_investment_amount": [4_000_000],
                        "municipality_count": [2],
                        "execution_project_count": [1],
                    }
                )
            if "vw_market_overview_current" in query:
                return pd.DataFrame(columns=gold.MARKET_OVERVIEW_COLUMNS)
            if "vw_project_location_current" in query:
                return pd.DataFrame(columns=gold.PROJECT_LOCATION_COLUMNS)
            return pd.DataFrame(columns=gold.STATUS_DISTRIBUTION_COLUMNS)

    monkeypatch.setenv("GOLD_DATABASE_URL", "postgresql+psycopg://test-only")
    monkeypatch.setattr(gold, "_connection", lambda: FakeConnection())
    gold.load_overview_data.clear()
    gold.load_overview_data()

    assert len(calls) == 4
    assert all("gold.vw_" in query and "_current" in query for query in calls)
    assert all("INSERT" not in query.upper() for query in calls)


def test_gold_contract_uses_explicit_selects_for_current_views() -> None:
    for view_name, (query, columns) in gold._VIEW_QUERIES.items():
        normalized = query.strip().upper()
        assert normalized.startswith("SELECT")
        assert f"FROM {view_name.upper()}" in normalized
        assert "SELECT *" not in normalized
        assert columns


def test_overview_filter_submission_updates_the_current_slice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from streamlit.testing.v1 import AppTest

    data = _overview_data()
    calls: list[tuple[tuple[str, ...], tuple[str, ...]]] = []

    monkeypatch.setattr(gold, "load_overview_data", lambda: data)

    def filtered_metrics(
        project_ids: tuple[str, ...],
        *,
        municipalities: tuple[str, ...] = (),
    ) -> gold.FilteredMetrics:
        calls.append((project_ids, municipalities))
        return gold.FilteredMetrics(
            kpis=pd.DataFrame(
                {
                    "project_count": [len(project_ids)],
                    "planned_investment_amount": [1_500_000],
                    "municipality_count": [len(municipalities)],
                    "execution_project_count": [len(project_ids)],
                }
            ),
            status_distribution=pd.DataFrame(
                {"source_status": ["Em execução"], "project_count": [len(project_ids)]}
            ),
        )

    monkeypatch.setattr(gold, "load_filtered_metrics", filtered_metrics)
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    app.multiselect[0].set_value(["Fortaleza"])
    app.button[0].click()
    app.run()

    assert not app.exception
    assert app.multiselect[0].value == ["Fortaleza"]
    assert calls[-1] == (("p-1",), ("Fortaleza",))
    assert app.metric[0].value == "1"
    assert len(app.dataframe[0].value) == 1


def test_overview_municipality_filter_keeps_project_pins_for_map() -> None:
    from frontend.pages import overview

    data = _overview_data()
    location = data.project_location.copy()
    location.loc[0, ["latitude", "longitude"]] = None
    pin = location.iloc[[0]].copy()
    pin["municipality_name"] = pd.NA
    pin["ibge_code"] = pd.NA
    pin["latitude"] = -3.73
    pin["longitude"] = -38.52
    location = pd.concat([location, pin], ignore_index=True)

    filtered_market, filtered_location = overview._apply_filters(
        data.market_overview,
        location,
        overview.FilterState(municipality=("Fortaleza",)),
    )

    assert filtered_market["project_id"].tolist() == ["p-1"]
    assert set(filtered_location["project_id"]) == {"p-1"}
    assert filtered_location[["latitude", "longitude"]].notna().all(axis=1).any()


def test_overview_uses_filtered_gold_metrics_for_kpis_and_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from frontend.pages import overview

    data = _overview_data()
    captured: dict[str, object] = {}

    monkeypatch.setattr(gold, "load_overview_data", lambda: data)
    monkeypatch.setattr(overview, "_render_styles", lambda: None)
    monkeypatch.setattr(overview, "_render_header", lambda _: None)
    monkeypatch.setattr(overview, "_render_partial_state", lambda *_: None)
    monkeypatch.setattr(
        overview,
        "_render_filters",
        lambda *_: overview.FilterState(status=("Em execução",)),
    )
    monkeypatch.setattr(
        overview,
        "_apply_filters",
        lambda market, location, _, **__: (market.iloc[[0]], location.iloc[[0]]),
    )

    def filtered_metrics(project_ids: tuple[str, ...], **_: object) -> gold.FilteredMetrics:
        captured["project_ids"] = project_ids
        return gold.FilteredMetrics(
            kpis=pd.DataFrame(
                {
                    "project_count": [1],
                    "planned_investment_amount": [1_500_000],
                    "municipality_count": [1],
                    "execution_project_count": [1],
                }
            ),
            status_distribution=pd.DataFrame(
                {"source_status": ["Em execução"], "project_count": [1]}
            ),
        )

    monkeypatch.setattr(gold, "load_filtered_metrics", filtered_metrics)
    monkeypatch.setattr(
        overview,
        "_render_kpis",
        lambda frame: captured.__setitem__("kpis", frame.copy()),
    )
    monkeypatch.setattr(
        overview,
        "_render_map",
        lambda frame: captured.__setitem__("map", frame.copy()),
    )
    monkeypatch.setattr(
        overview,
        "_render_status",
        lambda frame: captured.__setitem__("status", frame.copy()),
    )
    monkeypatch.setattr(overview, "_render_table", lambda _: None)

    overview.main()

    assert captured["project_ids"] == ("p-1",)
    assert captured["kpis"]["project_count"].iloc[0] == 1
    assert captured["map"]["project_id"].tolist() == ["p-1"]
    assert captured["status"]["source_status"].tolist() == ["Em execução"]


def test_registration_period_filter_uses_snapshot_reference_date() -> None:
    from datetime import date

    from frontend.pages import overview

    data = _overview_data()
    data.market_overview.loc[0, "registration_date"] = "2026-07-10"
    data.market_overview.loc[1, "registration_date"] = "2026-02-12"
    reference_date = date(2026, 8, 21)

    expected = {
        "Último mês": [],
        "Últimos 3 meses": ["p-1"],
        "Últimos 6 meses": ["p-1"],
        "Últimos 12 meses": ["p-1", "p-2"],
        "Ano corrente": ["p-1", "p-2"],
    }
    for period, project_ids in expected.items():
        filtered_market, _ = overview._apply_filters(
            data.market_overview,
            data.project_location,
            overview.FilterState(registration_period=(period,)),
            reference_date=reference_date,
        )
        assert filtered_market["project_id"].tolist() == project_ids
