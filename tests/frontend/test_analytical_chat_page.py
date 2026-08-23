from __future__ import annotations

from pathlib import Path

import pytest

from frontend.pages import analytical_chat

PAGE_PATH = Path(__file__).resolve().parents[2] / "frontend" / "pages" / "analytical_chat.py"
APP_PATH = Path(__file__).resolve().parents[2] / "frontend" / "streamlit_app.py"


def _app(monkeypatch: pytest.MonkeyPatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("ANALYTICAL_CHAT_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    return AppTest.from_file(str(PAGE_PATH), default_timeout=10)


def test_navigation_registers_chat_page() -> None:
    source = APP_PATH.read_text(encoding="utf-8")

    assert 'str(PAGES_DIR / "analytical_chat.py")' in source
    assert 'title="Chat com os dados"' in source


def test_chat_has_thinking_spinner() -> None:
    source = PAGE_PATH.read_text(encoding="utf-8")

    assert 'with st.spinner("Analisando os dados..."):' in source


def test_chat_is_disabled_by_default_without_provider_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ANALYTICAL_CHAT_ENABLED", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    from streamlit.testing.v1 import AppTest

    calls: list[str] = []
    app = AppTest.from_file(str(PAGE_PATH), default_timeout=10)
    app.session_state[analytical_chat.RUNNER_KEY] = lambda question, config: calls.append(question)
    app.run()

    assert not app.exception
    assert not app.warning
    assert any("temporariamente indisponível" in item.value for item in app.info)
    assert app.chat_input[0].disabled is True
    assert calls == []


def test_enabled_chat_does_not_require_transfer_checkbox(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    app = _app(monkeypatch)
    app.session_state[analytical_chat.RUNNER_KEY] = lambda question, config: calls.append(question)
    app.run()

    assert not app.exception
    assert len(app.checkbox) == 0
    assert app.chat_input[0].disabled is False
    assert calls == []


def test_missing_provider_configuration_is_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("ANALYTICAL_CHAT_ENABLED", "true")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    app = AppTest.from_file(str(PAGE_PATH), default_timeout=10).run()

    assert not app.exception
    assert any("temporariamente indisponível" in item.value for item in app.error)
    assert app.chat_input[0].disabled is True


def test_enabled_chat_renders_only_natural_language_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fake_runner(question: str, config: analytical_chat.ChatConfig) -> dict[str, object]:
        calls.append(question)
        return {
            "status": "ok",
            "answer": "Há duas obras no recorte atual.",
            "source_updated_at": "2026-08-21T00:00:00Z",
            "ingested_at": "2026-08-21T00:10:00Z",
            "sql": "SELECT count(DISTINCT project_id) FROM gold.vw_market_overview_current",
            "limits": ("máximo de 100 linhas",),
            "provenance": ("gold.vw_market_overview_current",),
            "truncated": True,
            "row_count": 2,
        }

    app = _app(monkeypatch)
    app.session_state[analytical_chat.RUNNER_KEY] = fake_runner
    app.run()
    app.chat_input[0].set_value("Quantas obras existem?")
    app.run()

    assert not app.exception
    assert calls == ["Quantas obras existem?"]
    assert any("Há duas obras" in item.value for item in app.markdown)
    assert not app.warning
    assert not app.code
    assert not any("Data de referência" in item.value for item in app.caption)
    assert not any("Proveniência" in item.value for item in app.caption)


def test_page_passes_previous_natural_turns_to_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, tuple[analytical_chat.ConversationTurn, ...]]] = []

    def contextual_runner(
        question: str,
        config: analytical_chat.ChatConfig,
        history: tuple[analytical_chat.ConversationTurn, ...],
    ) -> dict[str, object]:
        calls.append((question, history))
        return {"status": "answered", "answer": "Resposta contextual."}

    app = _app(monkeypatch)
    app.session_state[analytical_chat.RUNNER_KEY] = contextual_runner
    app.run()
    app.chat_input[0].set_value("Qual obra tem maior investimento?")
    app.run()
    app.chat_input[0].set_value("e em Fortaleza?")
    app.run()

    assert not app.exception
    assert calls[1][0] == "e em Fortaleza?"
    assert [turn.content for turn in calls[1][1]] == [
        "Qual obra tem maior investimento?",
        "Resposta contextual.",
    ]


def test_single_project_answer_renders_detail_link(monkeypatch: pytest.MonkeyPatch) -> None:
    def specific_project_runner(
        question: str, config: analytical_chat.ChatConfig
    ) -> dict[str, object]:
        return {
            "status": "ok",
            "answer": "A obra de maior valor foi identificada.",
            "result": {
                "columns": ("project_id", "planned_investment_amount"),
                "rows": (("obra 1/CE", 270600000),),
            },
        }

    app = _app(monkeypatch)
    app.session_state[analytical_chat.RUNNER_KEY] = specific_project_runner
    app.run()
    app.chat_input[0].set_value("Qual obra tem o maior valor?")
    app.run()

    assert not app.exception
    assert any("Ver detalhes da obra" in item.value for item in app.markdown)
    assert any("project_id=obra%201%2FCE" in item.value for item in app.markdown)


def test_greeting_is_rendered_as_chat_response_without_gold_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def greeting_runner(question: str, config: analytical_chat.ChatConfig) -> dict[str, object]:
        return {"status": "answered", "answer": "Olá! Posso ajudar com os dados."}

    app = _app(monkeypatch)
    app.session_state[analytical_chat.RUNNER_KEY] = greeting_runner
    app.run()
    app.chat_input[0].set_value("oi")
    app.run()

    assert not app.exception
    assert any("Olá! Posso ajudar" in item.value for item in app.markdown)
    assert not any("Proveniência" in item.value for item in app.caption)


def test_unsupported_question_does_not_render_gold_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unsupported_runner(
        question: str, config: analytical_chat.ChatConfig
    ) -> dict[str, object]:
        return {
            "status": "answered",
            "message": "Posso responder sobre obras, mas o snapshot não contém contratos.",
            "snapshot": {
                "source_updated_at": "2026-08-22T00:00:00+00:00",
                "ingested_at": "2026-08-22T18:34:51+00:00",
            },
        }

    app = _app(monkeypatch)
    app.session_state[analytical_chat.RUNNER_KEY] = unsupported_runner
    app.run()
    app.chat_input[0].set_value("Qual contrato custa mais?")
    app.run()

    assert not app.exception
    assert any("contratos" in item.value.lower() for item in app.markdown)
    assert not any("Data de referência" in item.value for item in app.caption)
    assert not any("Proveniência" in item.value for item in app.caption)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("outside_domain", "não pode ser respondida"),
        ("provider_unavailable", "tente novamente"),
        ("sql_rejected", "resposta segura"),
        ("timeout", "demorou"),
        ("gold_unavailable", "temporariamente indisponíveis"),
        ("empty", "não encontrei"),
    ],
)
def test_failure_states_are_distinct(status: str, expected: str) -> None:
    message = analytical_chat._status_message(analytical_chat.ChatResult(status=status))

    assert expected in message.lower()


def test_invalid_provider_configuration_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANALYTICAL_CHAT_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "codex_cli")

    config = analytical_chat._load_config()

    assert config.error == "provider_unsupported"


def test_normalization_does_not_expose_ingestion_id() -> None:
    result = analytical_chat._normalize_result(
        {
            "status": "ok",
            "answer": "Resposta",
            "ingestion_id": "secret-internal-id",
        }
    )

    assert not hasattr(result, "ingestion_id")
    assert result.provenance == ()


def test_adapter_maps_root_chat_envelope_without_internal_metadata() -> None:
    result = analytical_chat._normalize_result(
        {
            "status": "answered",
            "answer": "Resposta fundamentada.",
            "snapshot": {
                "source_updated_at": "2026-08-21T00:00:00Z",
                "ingested_at": "2026-08-21T00:10:00Z",
            },
            "result": {"rows": ((2,),), "truncated": True},
            "ingestion_id": "internal-id",
        }
    )

    assert result.status == "ok"
    assert result.source_updated_at == "2026-08-21T00:00:00Z"
    assert result.ingested_at == "2026-08-21T00:10:00Z"
    assert result.row_count == 1
    assert result.truncated is True
    assert not hasattr(result, "ingestion_id")


def test_single_project_result_exposes_detail_link_target() -> None:
    result = analytical_chat._normalize_result(
        {
            "status": "ok",
            "answer": "A obra encontrada foi a de maior valor.",
            "result": {
                "columns": ("project_id", "planned_investment_amount"),
                "rows": (("34727.23-28 (26.782.3106.13X6.0023)", 270600000),),
            },
        }
    )

    assert result.project_id == "34727.23-28 (26.782.3106.13X6.0023)"


def test_multiple_project_result_does_not_expose_detail_link_target() -> None:
    result = analytical_chat._normalize_result(
        {
            "status": "ok",
            "answer": "Foram encontradas duas obras.",
            "result": {
                "columns": ("project_id",),
                "rows": (("one",), ("two",)),
            },
        }
    )

    assert result.project_id is None


def test_flow_stops_on_sql_rejection(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def rejected(question: str, config: analytical_chat.ChatConfig) -> analytical_chat.ChatResult:
        calls.append(question)
        return analytical_chat.ChatResult(status="sql_rejected")

    monkeypatch.setattr(analytical_chat, "_run_chat", rejected)
    result = analytical_chat._execute_question(
        "Mostre as obras",
        analytical_chat.ChatConfig(True, "fake", "test"),
    )

    assert result.status == "sql_rejected"
    assert calls == ["Mostre as obras"]
