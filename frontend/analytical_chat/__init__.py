"""POC de chat analítico sobre as interfaces Gold públicas."""

from collections.abc import Sequence
from dataclasses import replace

from .agent import ChatAgent
from .config import AnalyticalChatConfig, load_config
from .context import (
    CATALOG_VIEW_NAMES,
    GENERATABLE_COLUMNS,
    GENERATABLE_VIEWS,
    GOLD_CATALOG,
    SemanticContext,
    build_semantic_context,
    classify_question,
)
from .contracts import (
    Answerability,
    ChatEnvelope,
    ChatStatus,
    ConversationTurn,
    GoldExecutor,
    GoldTimeoutError,
    LimitedResult,
    LLMProvider,
    QueryResult,
    SnapshotReference,
    SQLGenerationRequest,
    SQLProposal,
    SQLValidationEnvelope,
    SQLValidator,
    SynthesisEnvelope,
    SynthesisRequest,
)


class _GoldValidator:
    def __init__(self) -> None:
        from .sql_guard import SQLGuard

        self._guard = SQLGuard()

    def validate(self, sql: str) -> SQLValidationEnvelope:
        validated = self._guard.validate(sql)
        return SQLValidationEnvelope(accepted=True, sql=validated.sql)


class _GoldExecutor:
    def execute(self, approved_sql: str) -> QueryResult:
        from frontend import gold

        try:
            result = gold.execute_chat_query(approved_sql)
        except gold.GoldTimeoutError as exc:
            raise GoldTimeoutError("A consulta Gold excedeu o tempo limite.") from exc
        return QueryResult(
            columns=result.columns,
            rows=result.rows,
            truncated=result.truncated,
        )

    def resolve_project_id(self, result: LimitedResult) -> str | None:
        from frontend import gold

        columns = tuple(column.lower() for column in result.columns)
        if len(result.rows) != 1:
            return None
        row = result.rows[0]
        for field_name, resolver in (
            ("project_name", "project_name"),
            ("contract_source_id", "contract_source_id"),
        ):
            if field_name not in columns:
                continue
            value = row[columns.index(field_name)]
            if value is None:
                continue
            return gold.resolve_chat_project_id(**{resolver: str(value)})
        return None


def run_question(
    question: str,
    *,
    provider: str | None = None,
    model: str | None = None,
    conversation_history: Sequence[ConversationTurn] = (),
) -> ChatEnvelope:
    """Executa uma pergunta usando somente o provider e a Gold dedicados."""

    from .contracts import ChatConfigurationError, ChatStatus, ProviderError
    from .providers import create_provider

    try:
        bounded_history = tuple(conversation_history[-6:])
        config = load_config()
        if provider is not None or model is not None:
            config = replace(
                config,
                llm_provider=provider or config.llm_provider,
                gemini_model=model or config.gemini_model,
            )
        if not config.enabled:
            return ChatEnvelope(
                status=ChatStatus.DISABLED,
                message="Chat analítico desabilitado.",
                stage="config",
            )

        if config.gemini_api_key is None:
            try:
                import streamlit as st

                secret_key = st.secrets.get("GEMINI_API_KEY")
            except Exception:
                secret_key = None
            if secret_key:
                config = replace(config, gemini_api_key=str(secret_key))

        if classify_question(question, bounded_history) is not Answerability.RESPONDIBLE:
            return ChatAgent(
                None,
                _GoldValidator(),
                _GoldExecutor(),
                context=build_semantic_context(),
                config=config,
                conversation_history=bounded_history,
            ).ask(question)

        from frontend import gold

        try:
            metadata = gold.load_chat_snapshot_metadata()
        except gold.GoldTimeoutError:
            return ChatEnvelope(
                status=ChatStatus.TIMEOUT,
                message="A consulta Gold excedeu o tempo limite.",
                stage="snapshot_metadata",
            )
        snapshot = SnapshotReference.from_public_metadata(
            {
                "source_updated_at": metadata.source_updated_at if metadata else None,
                "ingested_at": metadata.ingested_at if metadata else None,
            }
        )
        selected_provider = create_provider(config)
        agent = ChatAgent(
            selected_provider,
            _GoldValidator(),
            _GoldExecutor(),
            context=build_semantic_context(snapshot),
            config=config,
            conversation_history=bounded_history,
        )
        return agent.ask(question)
    except ChatConfigurationError:
        return ChatEnvelope(
            status=ChatStatus.PROVIDER_ERROR,
            message="A configuração do chat está indisponível.",
            stage="config",
        )
    except ProviderError:
        return ChatEnvelope(
            status=ChatStatus.PROVIDER_ERROR,
            message="O provider está indisponível.",
            stage="provider",
        )
    except Exception:
        return ChatEnvelope(
            status=ChatStatus.GOLD_ERROR,
            message="A Gold está indisponível para esta pergunta.",
            stage="gold",
        )

__all__ = [
    "Answerability",
    "AnalyticalChatConfig",
    "CATALOG_VIEW_NAMES",
    "ChatAgent",
    "ChatEnvelope",
    "ChatStatus",
    "ConversationTurn",
    "GENERATABLE_COLUMNS",
    "GENERATABLE_VIEWS",
    "GOLD_CATALOG",
    "GoldExecutor",
    "GoldTimeoutError",
    "LLMProvider",
    "LimitedResult",
    "QueryResult",
    "SQLGenerationRequest",
    "SQLProposal",
    "SQLValidationEnvelope",
    "SQLValidator",
    "SemanticContext",
    "SnapshotReference",
    "SynthesisEnvelope",
    "SynthesisRequest",
    "build_semantic_context",
    "classify_question",
    "load_config",
    "run_question",
]
