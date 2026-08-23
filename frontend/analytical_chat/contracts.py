"""Contratos públicos do chat analítico, sem dependência de provider ou banco."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Protocol, Self


class Answerability(StrEnum):
    """Classificação da pergunta antes da execução de SQL."""

    RESPONDIBLE = "respondible"
    ANSWERABLE = "respondible"
    OUT_OF_DOMAIN = "out_of_domain"
    UNSUPPORTED = "unsupported"
    NOT_SUPPORTED = "unsupported"


class ChatStatus(StrEnum):
    """Estados apresentáveis pelo agente à página do Streamlit."""

    ANSWERED = "answered"
    DISABLED = "disabled"
    OUT_OF_DOMAIN = "out_of_domain"
    UNSUPPORTED = "unsupported"
    PROVIDER_ERROR = "provider_error"
    INVALID_PROVIDER_RESPONSE = "invalid_provider_response"
    SQL_REJECTED = "sql_rejected"
    TIMEOUT = "timeout"
    GOLD_ERROR = "gold_error"
    SYNTHESIS_ERROR = "synthesis_error"


class AnalyticalChatError(RuntimeError):
    """Erro seguro; detalhes internos não fazem parte do contrato público."""


class ChatConfigurationError(AnalyticalChatError):
    """Configuração ausente ou não permitida."""


class ProviderError(AnalyticalChatError):
    """Falha sanitizada de um provider."""


class ProviderConfigurationError(ProviderError):
    """Provider não instalado ou sem credencial/configuração necessária."""


class ProviderUnavailableError(ProviderError):
    """Provider indisponível, com timeout ou erro de transporte."""


class ProviderResponseError(ProviderError):
    """Resposta do provider fora do envelope estruturado esperado."""


class GoldTimeoutError(AnalyticalChatError):
    """Consulta Gold cancelada pelo timeout configurado."""


def _bounded_text(value: object, *, limit: int = 4_000) -> str:
    text = str(value).replace("\x00", "")
    return text[:limit]


@dataclass(frozen=True)
class ConversationTurn:
    """Turno natural limitado; nunca carrega SQL ou resultado bruto."""

    role: str
    content: str

    def __post_init__(self) -> None:
        role = str(self.role).strip().lower()
        if role not in {"user", "assistant"}:
            raise ValueError("Papel de conversa inválido.")
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "content", _bounded_text(self.content, limit=2_000).strip())


@dataclass(frozen=True)
class SnapshotReference:
    """Datas públicas do snapshot; nenhum identificador interno é transportado."""

    source_updated_at: str | None = None
    ingested_at: str | None = None

    @classmethod
    def from_public_metadata(cls, metadata: Mapping[str, object] | None) -> Self:
        if not metadata:
            return cls()
        return cls(
            source_updated_at=_public_date(metadata.get("source_updated_at")),
            ingested_at=_public_date(metadata.get("ingested_at")),
        )


def _public_date(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, str):
        return _bounded_text(value, limit=64)
    return None


@dataclass(frozen=True)
class SQLGenerationRequest:
    """Entrada mínima da primeira chamada do provider."""

    question: str
    semantic_context: str
    conversation_history: tuple[ConversationTurn, ...] = ()


@dataclass(frozen=True)
class SQLProposal:
    """Envelope estruturado de classificação e proposta de SQL."""

    answerability: Answerability
    sql: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "answerability", Answerability(self.answerability))
        if self.sql is not None:
            object.__setattr__(self, "sql", _bounded_text(self.sql, limit=20_000).strip())
        if self.reason is not None:
            object.__setattr__(self, "reason", _bounded_text(self.reason, limit=500).strip())
        if self.answerability is Answerability.RESPONDIBLE and not self.sql:
            raise ProviderResponseError("Proposta de SQL incompleta.")
        if self.answerability is not Answerability.RESPONDIBLE and self.sql:
            raise ProviderResponseError("Classificação não respondível contém SQL.")

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> Self:
        if "answerability" not in value:
            raise ProviderResponseError("Envelope de SQL sem classificação.")
        return cls(
            answerability=value["answerability"],
            sql=value.get("sql"),
            reason=value.get("reason"),
        )

    @classmethod
    def from_json(cls, text: str) -> Self:
        try:
            value = json.loads(text)
        except (TypeError, ValueError) as exc:
            raise ProviderResponseError("Envelope de SQL inválido.") from exc
        if not isinstance(value, Mapping):
            raise ProviderResponseError("Envelope de SQL inválido.")
        return cls.from_mapping(value)


@dataclass(frozen=True)
class SQLValidationEnvelope:
    """Resultado do validator injetado; somente SQL aprovado chega ao executor."""

    accepted: bool
    sql: str | None = None
    reason: str | None = None

    @property
    def approved(self) -> bool:
        return self.accepted


@dataclass(frozen=True)
class QueryResult:
    """Resultado já produzido pelo executor Gold injetado."""

    columns: tuple[str, ...]
    rows: tuple[tuple[object, ...], ...]
    truncated: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", tuple(str(column) for column in self.columns))
        object.__setattr__(self, "rows", tuple(tuple(row) for row in self.rows))

    @classmethod
    def from_value(cls, value: object) -> Self:
        if isinstance(value, cls):
            return value
        if isinstance(value, LimitedResult):
            return cls(value.columns, value.rows, value.truncated)
        if isinstance(value, Mapping):
            columns = tuple(str(column) for column in value.get("columns", ()))
            rows_value = value.get("rows", ())
            truncated = bool(value.get("truncated", False))
            return cls._from_rows(columns, rows_value, truncated)
        columns_value = getattr(value, "columns", ())
        columns = tuple(str(column) for column in columns_value)
        rows_value = (
            value.itertuples(index=False, name=None) if hasattr(value, "itertuples") else value
        )
        return cls._from_rows(columns, rows_value, bool(getattr(value, "truncated", False)))

    @classmethod
    def _from_rows(
        cls,
        columns: tuple[str, ...],
        rows_value: object,
        truncated: bool,
    ) -> Self:
        rows_list = (
            list(rows_value)
            if isinstance(rows_value, Sequence) or hasattr(rows_value, "__iter__")
            else []
        )
        if rows_list and isinstance(rows_list[0], Mapping):
            if not columns:
                columns = tuple(str(column) for column in rows_list[0])
            rows = [tuple(row.get(column) for column in columns) for row in rows_list]
        else:
            rows = [tuple(row) for row in rows_list]
        return cls(columns, tuple(rows), truncated)


@dataclass(frozen=True)
class LimitedResult:
    """Resultado seguro e limitado que pode atravessar a fronteira do provider."""

    columns: tuple[str, ...]
    rows: tuple[tuple[object, ...], ...]
    truncated: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", tuple(str(column) for column in self.columns))
        object.__setattr__(self, "rows", tuple(tuple(row) for row in self.rows))

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        return len(self.columns)

    def to_prompt_payload(self) -> dict[str, object]:
        return {
            "columns": list(self.columns),
            "rows": [list(row) for row in self.rows],
            "truncated": self.truncated,
        }


@dataclass(frozen=True)
class SynthesisRequest:
    """Entrada mínima da segunda chamada do provider."""

    question: str
    semantic_context: str
    approved_sql: str
    result: LimitedResult
    conversation_history: tuple[ConversationTurn, ...] = ()


@dataclass(frozen=True)
class SynthesisEnvelope:
    """Envelope estruturado da resposta final grounded no resultado Gold."""

    answer: str

    def __post_init__(self) -> None:
        answer = _bounded_text(self.answer, limit=20_000).strip()
        if not answer:
            raise ProviderResponseError("Síntese vazia.")
        object.__setattr__(self, "answer", answer)

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> Self:
        answer = value.get("answer")
        if not isinstance(answer, str):
            raise ProviderResponseError("Envelope de síntese inválido.")
        return cls(answer)

    @classmethod
    def from_json(cls, text: str) -> Self:
        try:
            value = json.loads(text)
        except (TypeError, ValueError) as exc:
            raise ProviderResponseError("Envelope de síntese inválido.") from exc
        if not isinstance(value, Mapping):
            raise ProviderResponseError("Envelope de síntese inválido.")
        return cls.from_mapping(value)


@dataclass(frozen=True)
class ChatEnvelope:
    """Retorno público esperado pela página; não contém erro interno ou segredo."""

    status: ChatStatus
    message: str
    answer: str | None = None
    sql: str | None = None
    result: LimitedResult | None = None
    answerability: Answerability | None = None
    snapshot: SnapshotReference | None = None
    stage: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", ChatStatus(self.status))
        object.__setattr__(self, "message", _bounded_text(self.message, limit=500))
        if self.answer is not None:
            object.__setattr__(self, "answer", _bounded_text(self.answer, limit=20_000))
        if self.sql is not None:
            object.__setattr__(self, "sql", _bounded_text(self.sql, limit=20_000))
        if self.answerability is not None:
            object.__setattr__(self, "answerability", Answerability(self.answerability))


class LLMProvider(Protocol):
    """Seam mínimo; providers não recebem conexão, shell, secrets ou ferramentas."""

    name: str

    def generate_sql(self, request: SQLGenerationRequest) -> SQLProposal:
        """Classifica a pergunta e, se respondível, propõe uma consulta."""

    def synthesize(self, request: SynthesisRequest) -> SynthesisEnvelope:
        """Redige resposta somente a partir da pergunta e do resultado limitado."""


class SQLValidator(Protocol):
    """Interface que o root deve ligar ao guard AST da Gold."""

    def validate(self, sql: str) -> SQLValidationEnvelope:
        """Valida e opcionalmente normaliza SQL antes da execução."""


class GoldExecutor(Protocol):
    """Interface que o root deve ligar ao executor Psycopg read-only."""

    def execute(self, approved_sql: str) -> QueryResult:
        """Executa somente SQL aprovado e devolve resultado limitado ou limitável."""


def _public_scalar(value: object, *, max_chars: int) -> object:
    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, date | datetime):
        return value.isoformat()
    if isinstance(value, Mapping | list | tuple | set):
        return "[valor estruturado omitido]"
    return _bounded_text(value, limit=max_chars)


def limit_result(
    value: object,
    *,
    max_rows: int = 100,
    max_columns: int = 20,
    max_bytes: int = 32_000,
    max_cell_chars: int = 1_000,
) -> LimitedResult:
    """Remove colunas internas e limita células, linhas, colunas e bytes."""

    result = QueryResult.from_value(value)
    public_indices = [
        index
        for index, column in enumerate(result.columns)
        if not _is_internal_column(column)
    ][:max_columns]
    columns = tuple(result.columns[index] for index in public_indices)
    rows: list[tuple[object, ...]] = []
    was_truncated = result.truncated or len(result.rows) > max_rows

    for source_row in result.rows[:max_rows]:
        row = tuple(
            _public_scalar(
                source_row[index] if index < len(source_row) else None,
                max_chars=max_cell_chars,
            )
            for index in public_indices
        )
        candidate = LimitedResult(columns, tuple(rows + [row]), was_truncated)
        encoded = json.dumps(
            candidate.to_prompt_payload(), ensure_ascii=False, default=str
        ).encode()
        if len(encoded) > max_bytes:
            was_truncated = True
            break
        rows.append(row)

    if len(public_indices) < len(result.columns):
        was_truncated = True
    return LimitedResult(columns, tuple(rows), was_truncated)


def _is_internal_column(column: str) -> bool:
    normalized = column.strip().lower()
    forbidden = (
        "ingestion_id",
        "secret",
        "password",
        "token",
        "credential",
        "connection",
        "schema",
        "payload",
        "raw",
    )
    return any(item in normalized for item in forbidden)


__all__ = [
    "Answerability",
    "AnalyticalChatError",
    "ChatConfigurationError",
    "ChatEnvelope",
    "ChatStatus",
    "ConversationTurn",
    "GoldExecutor",
    "GoldTimeoutError",
    "LLMProvider",
    "LimitedResult",
    "ProviderConfigurationError",
    "ProviderError",
    "ProviderResponseError",
    "ProviderUnavailableError",
    "QueryResult",
    "SQLGenerationRequest",
    "SQLProposal",
    "SQLValidationEnvelope",
    "SQLValidator",
    "SnapshotReference",
    "SynthesisEnvelope",
    "SynthesisRequest",
    "limit_result",
]
