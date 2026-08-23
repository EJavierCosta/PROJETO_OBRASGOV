"""Configuração fail-closed da capacidade de chat analítico."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from .contracts import ChatConfigurationError

SUPPORTED_LLM_PROVIDERS = frozenset({"gemini", "fake"})


@dataclass(frozen=True)
class AnalyticalChatConfig:
    """Valores operacionais sem incluir credencial na representação pública."""

    enabled: bool = False
    llm_provider: str = "gemini"
    gemini_api_key: str | None = field(default=None, repr=False)
    gemini_model: str = "gemini-3.5-flash-lite"
    provider_timeout_seconds: float = 30.0
    max_question_chars: int = 4_000
    max_result_rows: int = 100
    max_result_columns: int = 20
    max_result_bytes: int = 32_000
    max_cell_chars: int = 1_000

    def __post_init__(self) -> None:
        provider = str(self.llm_provider).strip().lower()
        if provider not in SUPPORTED_LLM_PROVIDERS:
            raise ChatConfigurationError("LLM_PROVIDER não suportado.")
        object.__setattr__(self, "llm_provider", provider)
        if not isinstance(self.enabled, bool):
            raise ChatConfigurationError("ANALYTICAL_CHAT_ENABLED inválido.")
        if not str(self.gemini_model).strip():
            raise ChatConfigurationError("GEMINI_MODEL inválido.")
        for name in (
            "provider_timeout_seconds",
            "max_question_chars",
            "max_result_rows",
            "max_result_columns",
            "max_result_bytes",
            "max_cell_chars",
        ):
            value = getattr(self, name)
            if value <= 0:
                raise ChatConfigurationError("Limite de configuração inválido.")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> AnalyticalChatConfig:
        values = env if env is not None else os.environ
        return cls(
            enabled=_read_bool(values, "ANALYTICAL_CHAT_ENABLED", default=False),
            llm_provider=values.get("LLM_PROVIDER", "gemini"),
            gemini_api_key=values.get("GEMINI_API_KEY") or None,
            gemini_model=values.get("GEMINI_MODEL", "gemini-3.5-flash-lite"),
            provider_timeout_seconds=_read_float(
                values,
                "ANALYTICAL_CHAT_PROVIDER_TIMEOUT_SECONDS",
                default=30.0,
            ),
            max_question_chars=_read_int(
                values,
                "ANALYTICAL_CHAT_MAX_QUESTION_CHARS",
                default=4_000,
            ),
            max_result_rows=_read_int(
                values,
                "ANALYTICAL_CHAT_MAX_RESULT_ROWS",
                default=100,
            ),
            max_result_columns=_read_int(
                values,
                "ANALYTICAL_CHAT_MAX_RESULT_COLUMNS",
                default=20,
            ),
            max_result_bytes=_read_int(
                values,
                "ANALYTICAL_CHAT_MAX_RESULT_BYTES",
                default=32_000,
            ),
            max_cell_chars=_read_int(
                values,
                "ANALYTICAL_CHAT_MAX_CELL_CHARS",
                default=1_000,
            ),
        )


def load_config(env: Mapping[str, str] | None = None) -> AnalyticalChatConfig:
    """Alias explícito usado pela página e pelos testes."""

    return AnalyticalChatConfig.from_env(env)


def _read_bool(env: Mapping[str, str], name: str, *, default: bool) -> bool:
    value = env.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "sim", "on"}:
        return True
    if normalized in {"0", "false", "no", "não", "nao", "off"}:
        return False
    raise ChatConfigurationError(f"{name} inválido.")


def _read_int(env: Mapping[str, str], name: str, *, default: int) -> int:
    value = env.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ChatConfigurationError(f"{name} inválido.") from exc


def _read_float(env: Mapping[str, str], name: str, *, default: float) -> float:
    value = env.get(name)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ChatConfigurationError(f"{name} inválido.") from exc


__all__ = [
    "SUPPORTED_LLM_PROVIDERS",
    "AnalyticalChatConfig",
    "load_config",
]
