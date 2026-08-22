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


def test_overview_app_smoke_without_database(monkeypatch: pytest.MonkeyPatch) -> None:
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(gold, "load_overview_data", lambda: _overview_data())
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
