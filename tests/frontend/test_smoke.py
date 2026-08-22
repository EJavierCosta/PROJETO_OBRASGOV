from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from frontend import gold

APP_PATH = Path(__file__).resolve().parents[2] / "frontend" / "streamlit_app.py"
DETAIL_PATH = Path(__file__).resolve().parents[2] / "frontend" / "pages" / "project_detail.py"


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
    assert any("Inteligência de Obras Públicas" in item.value for item in app.markdown)
    assert len(app.metric) == 4
    assert {item.label for item in app.metric} == {
        "Total de obras",
        "Investimento previsto",
        "Municípios alcançados",
        "Obras em execução",
    }
    period_filters = [
        item
        for item in app.selectbox
        if item.label == "Período da data de cadastro"
    ]
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


def test_overview_map_has_no_redundant_instruction_below_chart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(gold, "load_overview_data", lambda: _overview_data())
    monkeypatch.setattr(
        gold, "load_filtered_metrics", lambda *_args, **_kwargs: _filtered_metrics_data()
    )
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    assert not app.exception
    assert not any("Pontos representam municípios" in item.value for item in app.markdown)


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

    overview._render_status(
        pd.DataFrame({"source_status": ["Em execução"], "project_count": [3]})
    )

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
    assert any("Nenhum projeto corresponde" in item.value for item in app.info)


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
    assert any("Dados parciais" in item.value for item in app.markdown)
    assert any("Não informado" in str(item.value) for item in app.dataframe)


def test_project_detail_is_explicitly_out_of_scope() -> None:
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(DETAIL_PATH), default_timeout=10).run()

    assert not app.exception
    assert any("fora do escopo da SPEC-001" in item.value for item in app.info)


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
