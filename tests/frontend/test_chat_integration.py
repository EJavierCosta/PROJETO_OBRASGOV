from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from frontend import gold
from frontend.analytical_chat import GENERATABLE_COLUMNS, ChatStatus, run_question
from frontend.analytical_chat.sql_guard import (
    GENERATABLE_COLUMNS as GUARD_COLUMNS,
)
from frontend.analytical_chat.sql_guard import (
    validate_sql,
)


@dataclass(frozen=True)
class _Metadata:
    source_updated_at: str = "2026-08-21T00:00:00Z"
    ingested_at: str = "2026-08-22T00:10:00Z"


def test_run_question_integrates_fake_provider_guard_gold_and_snapshot(monkeypatch) -> None:
    monkeypatch.setenv("ANALYTICAL_CHAT_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.setattr(gold, "load_chat_snapshot_metadata", lambda: _Metadata())
    monkeypatch.setattr(
        gold,
        "execute_chat_query",
        lambda sql: gold.GoldQueryResult(
            columns=("project_count",),
            rows=((2,),),
        ),
    )

    result = run_question("Quantas obras existem?", provider="fake")

    assert result.status.value == "answered"
    assert result.answer == "Resposta determinística baseada no resultado Gold."
    assert result.sql is not None
    assert result.snapshot is not None
    assert result.snapshot.source_updated_at == _Metadata.source_updated_at
    assert result.result is not None
    assert result.result.rows == ((2,),)


def test_run_question_preserves_snapshot_timeout_state(monkeypatch) -> None:
    monkeypatch.setenv("ANALYTICAL_CHAT_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    def timeout_metadata() -> None:
        raise gold.GoldTimeoutError("internal")

    monkeypatch.setattr(gold, "load_chat_snapshot_metadata", timeout_metadata)

    result = run_question("Quantas obras existem?", provider="fake")

    assert result.status is ChatStatus.TIMEOUT
    assert result.stage == "snapshot_metadata"


def test_run_question_keeps_conversation_outside_gold(monkeypatch) -> None:
    monkeypatch.setenv("ANALYTICAL_CHAT_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    def metadata_must_not_run() -> None:
        raise AssertionError("conversa não deve consultar metadata Gold")

    monkeypatch.setattr(gold, "load_chat_snapshot_metadata", metadata_must_not_run)

    result = run_question("oi", provider="fake")

    assert result.status is ChatStatus.ANSWERED
    assert result.stage == "conversation"
    assert result.answer is not None


def test_semantic_catalog_is_the_single_generated_sql_allowlist() -> None:
    assert GUARD_COLUMNS == {
        view_name: frozenset(columns)
        for view_name, columns in GENERATABLE_COLUMNS.items()
    }
    assert all(
        "ingestion_id" not in columns
        for columns in GENERATABLE_COLUMNS.values()
    )


def test_semantic_columns_exist_in_dbt_contract() -> None:
    contract = (Path(__file__).parents[2] / "dbt/models/marts/_marts__models.yml").read_text(
        encoding="utf-8"
    )
    for view_name, columns in GENERATABLE_COLUMNS.items():
        model_name = view_name.rsplit(".", 1)[-1]
        block_start = contract.index(f"  - name: {model_name}")
        next_model = contract.find("\n  - name: ", block_start + 1)
        block = contract[block_start:] if next_model == -1 else contract[block_start:next_model]
        assert all(f"name: {column}" in block for column in columns)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT count(DISTINCT project_id) FROM gold.vw_market_overview_current",
        (
            "SELECT municipality_name, count(DISTINCT project_id) "
            "FROM gold.vw_project_location_current GROUP BY municipality_name"
        ),
        (
            "SELECT organization_name, count(DISTINCT project_id) "
            "FROM gold.vw_market_overview_current GROUP BY organization_name"
        ),
        (
            "SELECT organization_name, sum(planned_investment_amount) "
            "FROM gold.vw_market_overview_current GROUP BY organization_name"
        ),
        (
            "SELECT project_name, planned_investment_amount "
            "FROM gold.vw_market_overview_current ORDER BY planned_investment_amount DESC"
        ),
        (
            "SELECT count(DISTINCT project_id) FROM gold.vw_market_overview_current "
            "WHERE source_status = 'Em execução'"
        ),
        (
            "WITH locations AS ("
                "SELECT project_id FROM gold.vw_project_location_current "
                "WHERE municipality_name ILIKE '%Fortaleza%' GROUP BY project_id"
                "), execution_projects AS ("
                "SELECT project_id FROM gold.vw_project_execution_current "
                "WHERE physical_execution_percentage > 80 GROUP BY project_id"
            ") SELECT count(DISTINCT market.project_id) AS project_count "
            "FROM gold.vw_market_overview_current AS market "
            "INNER JOIN locations ON market.project_id = locations.project_id "
            "INNER JOIN execution_projects "
            "ON market.project_id = execution_projects.project_id "
            "WHERE market.source_status = 'Em execução'"
        ),
        "SELECT source_status, project_count FROM gold.vw_status_distribution_current",
        (
            "SELECT registration_year, count(DISTINCT project_id) "
            "FROM gold.vw_market_overview_current GROUP BY registration_year"
        ),
        (
            "SELECT COUNT(DISTINCT contract_source_id) AS total_contratos "
            "FROM gold.vw_project_contract_current"
        ),
        (
            "WITH locations AS ("
                "SELECT DISTINCT project_id FROM gold.vw_project_location_current "
                "WHERE municipality_name ILIKE '%Icapuí'"
                "), contracts AS ("
                "SELECT project_id, MAX(valor_global_contrato) AS maior_contrato "
                "FROM gold.vw_project_contract_current GROUP BY project_id"
                ") SELECT market.project_name, contracts.maior_contrato "
                "FROM locations "
                "INNER JOIN contracts ON locations.project_id = contracts.project_id "
                "INNER JOIN gold.vw_market_overview_current AS market "
                "ON locations.project_id = market.project_id "
                "ORDER BY contracts.maior_contrato DESC NULLS LAST LIMIT 1"
        ),
    ],
)
def test_golden_reference_sql_is_accepted(sql: str) -> None:
    assert validate_sql(sql).sql == sql
