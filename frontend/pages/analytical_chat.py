"""Página opcional de perguntas sobre obras públicas."""

from __future__ import annotations

import inspect
import os
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import streamlit as st

from frontend.analytical_chat.contracts import ConversationTurn

HISTORY_KEY = "analytical_chat_messages"
CHAT_INPUT_KEY = "analytical_chat_input"
RUNNER_KEY = "_analytical_chat_runner"
SUPPORTED_PROVIDERS = frozenset({"fake", "gemini"})
ENABLED_VALUES = frozenset({"1", "true", "yes", "on"})
DISABLED_VALUES = frozenset({"0", "false", "no", "off"})
RESULT_STATUSES = frozenset(
    {
        "ok",
        "config_missing",
        "empty",
        "outside_domain",
        "provider_unavailable",
        "sql_rejected",
        "timeout",
        "gold_unavailable",
        "invalid_response",
    }
)
STATUS_ALIASES = {
    "answered": "ok",
    "disabled": "config_missing",
    "unsupported": "outside_domain",
    "provider_error": "provider_unavailable",
    "invalid_provider_response": "invalid_response",
    "gold_error": "gold_unavailable",
    "synthesis_error": "provider_unavailable",
}


@dataclass(frozen=True)
class ChatConfig:
    enabled: bool
    provider: str
    model: str
    error: str | None = None


@dataclass(frozen=True)
class ChatResult:
    status: str = "ok"
    answer: str = ""
    source_updated_at: str | None = None
    ingested_at: str | None = None
    sql: str | None = None
    limits: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    truncated: bool = False
    row_count: int | None = None
    project_id: str | None = None


class ChatError(RuntimeError):
    """Erro seguro que o adapter local pode devolver à página."""

    def __init__(self, status: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def _secret_is_configured(name: str) -> bool:
    if os.getenv(name):
        return True
    try:
        return bool(st.secrets.get(name))
    except Exception:
        return False


def _load_config() -> ChatConfig:
    enabled_value = os.getenv("ANALYTICAL_CHAT_ENABLED")
    enabled = (enabled_value or "").strip().lower() in ENABLED_VALUES
    if enabled_value and enabled_value.strip().lower() not in ENABLED_VALUES | DISABLED_VALUES:
        return ChatConfig(False, "", "", "invalid_enabled")
    if not enabled:
        return ChatConfig(False, "", "")

    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
    if not provider:
        return ChatConfig(True, "", model, "provider_missing")
    if provider not in SUPPORTED_PROVIDERS:
        return ChatConfig(True, provider, model, "provider_unsupported")
    if provider == "gemini" and not _secret_is_configured("GEMINI_API_KEY"):
        return ChatConfig(True, provider, model, "credential_missing")
    return ChatConfig(True, provider, model)


def _run_chat(
    question: str,
    config: ChatConfig,
    conversation_history: tuple[ConversationTurn, ...] = (),
) -> ChatResult | Mapping[str, Any]:
    """Adapter local para a API do ChatAgent que o root deve integrar."""
    injected_runner = st.session_state.get(RUNNER_KEY)
    if callable(injected_runner):
        try:
            parameters = tuple(inspect.signature(injected_runner).parameters.values())
        except (TypeError, ValueError):
            parameters = ()
        accepts_history = any(
            parameter.kind is inspect.Parameter.VAR_POSITIONAL for parameter in parameters
        ) or len(parameters) >= 3
        if accepts_history:
            return injected_runner(question, config, conversation_history)
        return injected_runner(question, config)
    try:
        from frontend.analytical_chat import run_question
    except (ImportError, AttributeError) as exc:
        raise ChatError(
            "provider_unavailable",
            "O provider do chat está indisponível nesta instalação.",
        ) from exc
    return run_question(
        question,
        provider=config.provider,
        model=config.model,
        conversation_history=conversation_history,
    )


def _as_text_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if isinstance(value, Sequence):
        return tuple(str(item) for item in value if str(item).strip())
    return (str(value),)


def _single_project_id(value: Any) -> str | None:
    if value is None or _field(value, "truncated", False):
        return None
    columns = tuple(str(column).strip().lower() for column in _field(value, "columns", ()))
    if "project_id" not in columns:
        return None
    rows = _field(value, "rows", ())
    if len(rows) != 1:
        return None
    index = columns.index("project_id")
    row = rows[0]
    if index >= len(row) or row[index] is None:
        return None
    project_id = str(row[index]).strip()
    return project_id[:200] if project_id else None


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _normalize_result(value: Any) -> ChatResult:
    if isinstance(value, ChatResult):
        result = value
    else:
        raw_status = str(_field(value, "status", "")).lower()
        status = STATUS_ALIASES.get(raw_status, raw_status)
        snapshot = _field(value, "snapshot")
        limited_result = _field(value, "result")
        raw_answer = _field(value, "answer") or _field(value, "message", "")
        raw_row_count = _field(value, "row_count")
        if raw_row_count is None and limited_result is not None:
            rows = _field(limited_result, "rows", ())
            raw_row_count = len(rows)
        raw_truncated = _field(value, "truncated", False)
        if limited_result is not None:
            raw_truncated = raw_truncated or _field(limited_result, "truncated", False)
        result = ChatResult(
            status=status,
            answer=str(raw_answer),
            source_updated_at=_field(value, "source_updated_at")
            or _field(snapshot, "source_updated_at"),
            ingested_at=_field(value, "ingested_at") or _field(snapshot, "ingested_at"),
            sql=_field(value, "sql"),
            limits=_as_text_tuple(_field(value, "limits")),
            provenance=_as_text_tuple(_field(value, "provenance")),
            truncated=bool(raw_truncated),
            row_count=raw_row_count,
            project_id=_single_project_id(limited_result),
        )
    if result.status not in RESULT_STATUSES:
        raise ChatError("invalid_response", "O provider devolveu uma resposta inválida.")
    if result.status == "ok" and not result.answer.strip():
        raise ChatError("invalid_response", "O provider devolveu uma resposta vazia.")
    return result


def _execute_question(
    question: str,
    config: ChatConfig,
    conversation_history: tuple[ConversationTurn, ...] = (),
    last_project_id: str | None = None,
) -> ChatResult:
    if last_project_id and _is_link_followup(question):
        return ChatResult(
            status="ok",
            answer="O link para a obra mencionada anteriormente está disponível abaixo.",
            project_id=last_project_id,
        )
    try:
        try:
            parameters = tuple(inspect.signature(_run_chat).parameters.values())
        except (TypeError, ValueError):
            parameters = ()
        if len(parameters) >= 3:
            value = _run_chat(question, config, conversation_history)
        else:
            value = _run_chat(question, config)
        return _normalize_result(value)
    except ChatError as exc:
        return ChatResult(status=exc.status, answer=exc.message)
    except TimeoutError:
        return ChatResult(
            status="timeout",
        )
    except Exception as exc:
        status = getattr(exc, "status", "provider_unavailable")
        if status not in RESULT_STATUSES:
            status = "provider_unavailable"
        return ChatResult(
            status=status,
            answer="Não foi possível concluir a consulta do chat.",
        )


def _status_message(result: ChatResult) -> str:
    messages = {
        "outside_domain": "Essa pergunta não pode ser respondida com as informações disponíveis.",
        "config_missing": "O chat está indisponível no momento.",
        "provider_unavailable": "Não foi possível responder agora. Tente novamente em instantes.",
        "sql_rejected": "Não foi possível encontrar uma resposta segura para essa pergunta.",
        "timeout": "A consulta demorou mais que o esperado. Tente novamente.",
        "gold_unavailable": "Os dados estão temporariamente indisponíveis. Tente novamente.",
        "invalid_response": "Não foi possível preparar uma resposta agora. Tente novamente.",
        "empty": "Não encontrei informações para essa pergunta.",
    }
    if result.status == "ok" and result.answer.strip():
        return result.answer.strip()
    return messages.get(result.status, "Não foi possível responder à pergunta.")


def _render_result(result: ChatResult) -> None:
    if result.status == "ok":
        st.markdown(result.answer)
        if result.project_id:
            st.markdown(
                f"[Ver detalhes da obra](project_detail?project_id="
                f"{quote(result.project_id, safe='')})"
            )
    elif result.status == "empty":
        st.info(_status_message(result))
    elif result.status == "outside_domain":
        st.info(_status_message(result))
    else:
        st.error(_status_message(result))


def _conversation_history() -> tuple[ConversationTurn, ...]:
    turns: list[ConversationTurn] = []
    for message in st.session_state[HISTORY_KEY]:
        role = message.get("role")
        content = message.get("content", "")
        if role in {"user", "assistant"} and str(content).strip():
            turns.append(ConversationTurn(str(role), str(content)))
    return tuple(turns[-6:])


def _last_project_id() -> str | None:
    for message in reversed(st.session_state[HISTORY_KEY]):
        if message.get("role") != "assistant" or "result" not in message:
            continue
        try:
            project_id = _normalize_result(message["result"]).project_id
        except ChatError:
            continue
        if project_id:
            return project_id
    return None


def _is_link_followup(question: str) -> bool:
    normalized = unicodedata.normalize("NFKD", question.lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    words = normalized.split()
    return "link" in words and len(words) <= 5


def _render_history() -> None:
    for message in st.session_state[HISTORY_KEY]:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and "result" in message:
                _render_result(_normalize_result(message["result"]))
            else:
                st.markdown(message["content"])


def _append_message(role: str, content: str, result: ChatResult | None = None) -> None:
    message: dict[str, Any] = {"role": role, "content": content}
    if result is not None:
        message["result"] = result
    st.session_state[HISTORY_KEY].append(message)


def _render_configuration_state(config: ChatConfig) -> bool:
    if config.error == "invalid_enabled":
        st.error("O chat está temporariamente indisponível.")
    elif not config.enabled:
        st.info("O chat está temporariamente indisponível.")
    elif config.error == "provider_missing":
        st.error("O chat está temporariamente indisponível.")
    elif config.error == "provider_unsupported":
        st.error("O chat está temporariamente indisponível.")
    elif config.error == "credential_missing":
        st.error("O chat está temporariamente indisponível.")
    return config.enabled and config.error is None


def main() -> None:
    st.title("Chat com os dados")
    st.caption(
        "Converse livremente sobre obras, organizações, situação e investimentos previstos "
        "no Ceará."
    )
    st.session_state.setdefault(HISTORY_KEY, [])

    config = _load_config()
    available = _render_configuration_state(config)
    _render_history()

    question = st.chat_input(
        "Escreva uma mensagem ou pergunte sobre os dados...",
        key=CHAT_INPUT_KEY,
        disabled=not available,
    )
    if not question or not available:
        return

    clean_question = question.strip()
    if not clean_question:
        return
    conversation_history = _conversation_history()
    last_project_id = _last_project_id()
    _append_message("user", clean_question)
    with st.chat_message("user"):
        st.markdown(clean_question)

    with st.spinner("Analisando os dados..."):
        result = _execute_question(
            clean_question,
            config,
            conversation_history,
            last_project_id,
        )
    _append_message("assistant", _status_message(result), result)
    with st.chat_message("assistant"):
        _render_result(result)


main()
