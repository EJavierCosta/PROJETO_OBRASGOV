"""Orquestração segura do chat sem conhecer SDK, parser ou banco."""

from __future__ import annotations

from collections.abc import Mapping

from .config import AnalyticalChatConfig
from .context import SemanticContext, build_semantic_context, classify_question, is_greeting
from .contracts import (
    Answerability,
    ChatEnvelope,
    ChatStatus,
    ConversationTurn,
    GoldExecutor,
    GoldTimeoutError,
    LimitedResult,
    LLMProvider,
    ProviderConfigurationError,
    ProviderError,
    ProviderResponseError,
    QueryResult,
    SQLGenerationRequest,
    SQLProposal,
    SQLValidationEnvelope,
    SQLValidator,
    SynthesisEnvelope,
    SynthesisRequest,
    limit_result,
)


class ChatAgent:
    """Fluxo público pergunta → SQL → validação → Gold → síntese.

    A página consome :class:`ChatEnvelope`. O root integra ``SQLValidator`` ao
    guard AST e ``GoldExecutor`` ao executor read-only; ambos entram por injeção
    e não são implementados neste módulo.
    """

    def __init__(
        self,
        provider: LLMProvider | None,
        validator: SQLValidator,
        executor: GoldExecutor,
        *,
        context: SemanticContext | None = None,
        config: AnalyticalChatConfig | None = None,
        conversation_history: tuple[ConversationTurn, ...] = (),
    ) -> None:
        self.provider = provider
        self.validator = validator
        self.executor = executor
        self.context = context or build_semantic_context()
        self.config = config or AnalyticalChatConfig(enabled=True)
        self.conversation_history = tuple(conversation_history[-6:])

    def ask(self, question: str) -> ChatEnvelope:
        """Processa uma pergunta sem repetir SQL nem fazer fallback automático."""

        if not self.config.enabled:
            return self._failure(
                ChatStatus.DISABLED,
                "Chat analítico desabilitado.",
                stage="config",
            )

        normalized_question = _bounded_question(question, self.config.max_question_chars)
        initial_answerability = classify_question(
            normalized_question,
            self.conversation_history,
        )
        if initial_answerability is not Answerability.RESPONDIBLE:
            return self._answerability_failure(initial_answerability, normalized_question)

        try:
            proposal_value = self.provider.generate_sql(
                SQLGenerationRequest(
                    question=normalized_question,
                    semantic_context=self.context.render_for_provider(),
                    conversation_history=self.conversation_history,
                )
            )
            proposal = _coerce_proposal(proposal_value)
        except ProviderConfigurationError:
            return self._failure(
                ChatStatus.PROVIDER_ERROR,
                "A configuração do Gemini foi rejeitada. Revise GEMINI_API_KEY e GEMINI_MODEL.",
                stage="sql_generation",
            )
        except ProviderResponseError:
            return self._failure(
                ChatStatus.INVALID_PROVIDER_RESPONSE,
                "O provider retornou uma proposta inválida.",
                stage="sql_generation",
            )
        except ProviderError:
            return self._failure(
                ChatStatus.PROVIDER_ERROR,
                "Não foi possível consultar o provider.",
                stage="sql_generation",
            )
        except Exception:
            return self._failure(
                ChatStatus.PROVIDER_ERROR,
                "Não foi possível consultar o provider.",
                stage="sql_generation",
            )

        if proposal.answerability is not Answerability.RESPONDIBLE:
            return self._answerability_failure(proposal.answerability, normalized_question)

        try:
            validation = _coerce_validation(self.validator.validate(proposal.sql or ""))
        except Exception:
            return self._failure(
                ChatStatus.SQL_REJECTED,
                "A consulta não passou pela validação.",
                sql=proposal.sql,
                stage="sql_validation",
            )
        if not validation.accepted:
            return self._failure(
                ChatStatus.SQL_REJECTED,
                "A consulta proposta foi rejeitada.",
                sql=proposal.sql,
                stage="sql_validation",
            )

        approved_sql = validation.sql or proposal.sql
        if not isinstance(approved_sql, str) or not approved_sql.strip():
            return self._failure(
                ChatStatus.SQL_REJECTED,
                "A validação não devolveu SQL aprovado.",
                stage="sql_validation",
            )

        try:
            raw_result = self.executor.execute(approved_sql)
            result = limit_result(
                QueryResult.from_value(raw_result),
                max_rows=self.config.max_result_rows,
                max_columns=self.config.max_result_columns,
                max_bytes=self.config.max_result_bytes,
                max_cell_chars=self.config.max_cell_chars,
            )
        except GoldTimeoutError:
            return self._failure(
                ChatStatus.TIMEOUT,
                "A consulta Gold excedeu o tempo limite.",
                sql=approved_sql,
                stage="gold_execution",
            )
        except Exception:
            return self._failure(
                ChatStatus.GOLD_ERROR,
                "Não foi possível consultar a Gold.",
                sql=approved_sql,
                stage="gold_execution",
            )

        try:
            synthesis_value = self.provider.synthesize(
                SynthesisRequest(
                    question=normalized_question,
                    semantic_context=self.context.render_for_provider(),
                    approved_sql=approved_sql,
                    result=result,
                    conversation_history=self.conversation_history,
                )
            )
            synthesis = _coerce_synthesis(synthesis_value)
        except ProviderResponseError:
            return self._failure(
                ChatStatus.INVALID_PROVIDER_RESPONSE,
                "O provider retornou uma síntese inválida.",
                sql=approved_sql,
                result=result,
                stage="synthesis",
            )
        except ProviderError:
            return self._failure(
                ChatStatus.SYNTHESIS_ERROR,
                "Não foi possível sintetizar a resposta.",
                sql=approved_sql,
                result=result,
                stage="synthesis",
            )
        except Exception:
            return self._failure(
                ChatStatus.SYNTHESIS_ERROR,
                "Não foi possível sintetizar a resposta.",
                sql=approved_sql,
                result=result,
                stage="synthesis",
            )

        return ChatEnvelope(
            status=ChatStatus.ANSWERED,
            message="Resposta gerada a partir do resultado Gold.",
            answer=synthesis.answer,
            sql=approved_sql,
            result=result,
            answerability=Answerability.RESPONDIBLE,
            snapshot=self.context.snapshot,
            stage="completed",
        )

    run = ask

    def _answerability_failure(self, answerability: Answerability, question: str) -> ChatEnvelope:
        if answerability is Answerability.UNSUPPORTED:
            message = "Não consigo responder essa pergunta com as informações disponíveis."
        else:
            if is_greeting(question):
                message = (
                    "Olá! Posso ajudar com obras, organizações, situação e investimento "
                    "previsto no Ceará."
                )
            else:
                message = (
                    "Posso ajudar com segurança apenas com informações públicas sobre obras do "
                    "Ceará. Pergunte sobre obras, organizações, situação ou investimento previsto."
                )
        return ChatEnvelope(
            status=ChatStatus.ANSWERED,
            message=message,
            answer=message,
            answerability=answerability,
            snapshot=self.context.snapshot,
            stage="conversation",
        )

    def _failure(
        self,
        status: ChatStatus,
        message: str,
        *,
        sql: str | None = None,
        result: LimitedResult | None = None,
        stage: str,
    ) -> ChatEnvelope:
        return ChatEnvelope(
            status=status,
            message=message,
            sql=sql,
            result=result,
            snapshot=self.context.snapshot,
            stage=stage,
        )


def _bounded_question(question: str, limit: int) -> str:
    if not isinstance(question, str):
        return ""
    return question.replace("\x00", "").strip()[:limit]


def _coerce_proposal(value: object) -> SQLProposal:
    if isinstance(value, SQLProposal):
        return value
    if isinstance(value, Mapping):
        return SQLProposal.from_mapping(value)
    raise ProviderResponseError("Proposta de SQL inválida.")


def _coerce_validation(value: object) -> SQLValidationEnvelope:
    if isinstance(value, SQLValidationEnvelope):
        return value
    if isinstance(value, bool):
        return SQLValidationEnvelope(accepted=value)
    if isinstance(value, Mapping):
        accepted = value.get("accepted", value.get("approved", False))
        if not isinstance(accepted, bool):
            raise ValueError("Resultado de validação inválido.")
        sql = value.get("sql")
        return SQLValidationEnvelope(accepted=accepted, sql=sql if isinstance(sql, str) else None)
    accepted = getattr(value, "accepted", getattr(value, "approved", None))
    if not isinstance(accepted, bool):
        raise ValueError("Resultado de validação inválido.")
    sql = getattr(value, "sql", None)
    return SQLValidationEnvelope(accepted=accepted, sql=sql if isinstance(sql, str) else None)


def _coerce_synthesis(value: object) -> SynthesisEnvelope:
    if isinstance(value, SynthesisEnvelope):
        return value
    if isinstance(value, Mapping):
        return SynthesisEnvelope.from_mapping(value)
    raise ProviderResponseError("Síntese inválida.")


__all__ = ["ChatAgent"]
