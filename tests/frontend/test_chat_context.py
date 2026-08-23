from __future__ import annotations

from frontend.analytical_chat.context import (
    CATALOG_VIEW_NAMES,
    GENERATABLE_COLUMNS,
    GOLD_CATALOG,
    build_semantic_context,
    classify_question,
    is_greeting,
)
from frontend.analytical_chat.contracts import (
    Answerability,
    ConversationTurn,
    QueryResult,
    SnapshotReference,
    limit_result,
)


def test_context_catalog_has_five_public_views_and_no_internal_id() -> None:
    context = build_semantic_context(
        SnapshotReference(source_updated_at="2026-08-21T00:00:00Z")
    )
    rendered = context.render_for_provider()

    assert len(GOLD_CATALOG) == 18
    assert len(CATALOG_VIEW_NAMES) == 18
    assert len(GENERATABLE_COLUMNS) == 17
    assert "gold.vw_snapshot_metadata_current" not in GENERATABLE_COLUMNS
    assert "gold.vw_snapshot_metadata_current" in CATALOG_VIEW_NAMES
    assert all("ingestion_id" not in columns for columns in GENERATABLE_COLUMNS.values())
    assert "source_updated_at=2026-08-21T00:00:00Z" in rendered
    assert "ingestion_id" not in rendered
    assert "schema discovery" not in rendered.lower()


def test_question_classification_recuses_unsupported_and_out_of_domain() -> None:
    assert classify_question("Quantas obras estão em execução?") is Answerability.RESPONDIBLE
    assert classify_question("Quais contratos foram pagos?") is Answerability.RESPONDIBLE
    assert classify_question("Quais empenhos foram liquidados?") is Answerability.RESPONDIBLE
    assert (
        classify_question("Quais fornecedores aparecem nos contratos?")
        is Answerability.RESPONDIBLE
    )
    assert classify_question("Quais estudos e históricos existem?") is Answerability.RESPONDIBLE
    assert classify_question("Quais obras estão atrasadas?") is Answerability.UNSUPPORTED
    assert classify_question("Qual é a capital da França?") is Answerability.OUT_OF_DOMAIN
    assert classify_question("Qual o investimento por município?") is Answerability.UNSUPPORTED
    assert (
        classify_question(
            "qunta obras estao ativas hj em fortaleza com porcentagem de conclusao acima de 80%"
        )
        is Answerability.RESPONDIBLE
    )


def test_context_describes_execution_status_and_percentage_rule() -> None:
    rendered = build_semantic_context().render_for_provider()

    assert "source_status = 'Em execução'" in rendered
    assert "physical_execution_percentage" in rendered
    assert "conte DISTINCT project_id" in rendered


def test_question_classification_uses_previous_turn_for_follow_up() -> None:
    history = (ConversationTurn("user", "Qual obra tem maior investimento?"),)

    assert classify_question("e em Fortaleza?", history) is Answerability.RESPONDIBLE


def test_greeting_is_conversational_without_becoming_a_gold_question() -> None:
    assert is_greeting("oi") is True
    assert is_greeting("Bom dia, tudo bem?") is True
    assert is_greeting("Quantas obras existem?") is False


def test_limited_result_removes_internal_columns_and_bounds_output() -> None:
    result = QueryResult(
        columns=("project_id", "ingestion_id", "description", "payload"),
        rows=(
            ("p-1", "internal", "A" * 500, {"raw": "data"}),
            ("p-2", "internal", "segunda", {"raw": "data"}),
        ),
    )

    limited = limit_result(result, max_rows=1, max_columns=5, max_bytes=2_000, max_cell_chars=20)

    assert limited.columns == ("project_id", "description")
    assert limited.rows == (("p-1", "A" * 20),)
    assert limited.truncated is True
    assert "ingestion_id" not in str(limited.to_prompt_payload())
