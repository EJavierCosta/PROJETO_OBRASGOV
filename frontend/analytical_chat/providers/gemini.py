"""Adapter oficial Google GenAI, lazy e testável sem chamadas de rede."""

from __future__ import annotations

from typing import Any

from ..contracts import (
    ProviderConfigurationError,
    ProviderResponseError,
    ProviderUnavailableError,
    SQLGenerationRequest,
    SQLProposal,
    SynthesisEnvelope,
    SynthesisRequest,
)
from .base import build_sql_prompt, build_synthesis_prompt


class GeminiProvider:
    """Implementa o seam público usando somente ``google-genai``."""

    name = "gemini"

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = "gemini-3.5-flash-lite",
        timeout_seconds: float = 30.0,
        client: Any | None = None,
    ) -> None:
        if not model.strip():
            raise ProviderConfigurationError("GEMINI_MODEL inválido.")
        if timeout_seconds <= 0:
            raise ProviderConfigurationError("Timeout do provider inválido.")
        if client is None and not api_key:
            raise ProviderConfigurationError("GEMINI_API_KEY não configurada.")
        self.model = model.strip()
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._client = client
        self._config_factory: Any | None = None

    def generate_sql(self, request: SQLGenerationRequest) -> SQLProposal:
        response = self._generate(build_sql_prompt(request), SQL_RESPONSE_SCHEMA)
        try:
            return SQLProposal.from_json(_response_text(response))
        except ProviderResponseError:
            raise
        except Exception as exc:
            raise ProviderResponseError("Envelope de SQL inválido.") from exc

    def synthesize(self, request: SynthesisRequest) -> SynthesisEnvelope:
        response = self._generate(build_synthesis_prompt(request), SYNTHESIS_RESPONSE_SCHEMA)
        try:
            return SynthesisEnvelope.from_json(_response_text(response))
        except ProviderResponseError:
            raise
        except Exception as exc:
            raise ProviderResponseError("Envelope de síntese inválido.") from exc

    def _generate(self, prompt: str, response_schema: dict[str, Any]) -> Any:
        client = self._get_client()
        kwargs: dict[str, Any] = {"model": self.model, "contents": prompt}
        if self._config_factory is not None:
            kwargs["config"] = self._config_factory(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0,
                seed=42,
            )
        try:
            return client.models.generate_content(**kwargs)
        except ProviderUnavailableError:
            raise
        except Exception as exc:
            if _is_access_configuration_error(exc):
                raise ProviderConfigurationError(
                    "Credencial Gemini inválida ou sem acesso ao modelo configurado."
                ) from exc
            raise ProviderUnavailableError("Provider Gemini indisponível.") from exc

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if not self._api_key:
            raise ProviderConfigurationError("GEMINI_API_KEY não configurada.")
        try:
            from google import genai
            from google.genai import types
        except (ImportError, ModuleNotFoundError) as exc:
            raise ProviderConfigurationError("SDK Google GenAI indisponível.") from exc
        try:
            timeout_ms = int(self._timeout_seconds * 1_000)
            http_options = types.HttpOptions(timeout=timeout_ms)
            self._config_factory = types.GenerateContentConfig
            self._client = genai.Client(api_key=self._api_key, http_options=http_options)
            return self._client
        except Exception as exc:
            raise ProviderUnavailableError("Provider Gemini indisponível.") from exc


def _response_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text
    candidates = getattr(response, "candidates", None) or ()
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", None) or ():
            text = getattr(part, "text", None)
            if isinstance(text, str) and text.strip():
                return text
    raise ProviderResponseError("Resposta Gemini sem texto.")


def _is_access_configuration_error(error: BaseException) -> bool:
    """Identifica falhas de credencial/modelo sem transportar o erro bruto."""

    current: BaseException | None = error
    for _ in range(4):
        if current is None:
            break
        message = str(current).lower()
        if any(
            marker in message
            for marker in ("404", "not_found", "401", "unauthorized", "403", "forbidden")
        ):
            return True
        current = current.__cause__ or current.__context__
    return False


SQL_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "answerability": {
            "type": "STRING",
            "enum": ["respondible", "unsupported", "out_of_domain"],
        },
        "sql": {"type": "STRING"},
        "reason": {"type": "STRING"},
    },
    "required": ["answerability", "sql", "reason"],
}

SYNTHESIS_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {"answer": {"type": "STRING"}},
    "required": ["answer"],
}


__all__ = ["GeminiProvider"]
