from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from frontend.analytical_chat.config import AnalyticalChatConfig, load_config
from frontend.analytical_chat.contracts import (
    Answerability,
    ChatConfigurationError,
    LimitedResult,
    ProviderConfigurationError,
    ProviderResponseError,
    ProviderUnavailableError,
    SQLGenerationRequest,
    SynthesisRequest,
)
from frontend.analytical_chat.providers import FakeProvider, GeminiProvider, create_provider
from frontend.analytical_chat.providers.base import build_sql_prompt, build_synthesis_prompt


def test_config_is_disabled_by_default_and_rejects_codex_cli() -> None:
    config = load_config({})

    assert config.enabled is False
    assert config.llm_provider == "gemini"
    with pytest.raises(ChatConfigurationError):
        load_config({"LLM_PROVIDER": "codex_cli"})


def test_factory_supports_only_fake_and_gemini() -> None:
    fake = create_provider(AnalyticalChatConfig(llm_provider="fake"))
    assert isinstance(fake, FakeProvider)

    with pytest.raises(ProviderConfigurationError):
        create_provider(AnalyticalChatConfig(llm_provider="gemini"))


def test_fake_provider_can_return_non_respondible_classification() -> None:
    provider = FakeProvider(answerability=Answerability.UNSUPPORTED)

    proposal = provider.generate_sql(
        SQLGenerationRequest(question="Contratos?", semantic_context="Gold")
    )

    assert proposal.answerability is Answerability.UNSUPPORTED
    assert proposal.sql is None


def test_sql_prompt_covers_contract_counts_and_safe_top_results() -> None:
    prompt = build_sql_prompt(
        SQLGenerationRequest(
            question="Quantos contratos temos no Ceará?",
            semantic_context="Gold pública do Ceará",
        )
    )

    assert "COUNT(DISTINCT contract_source_id)" in prompt
    assert "não faça JOIN com localização ou visão geral" in prompt
    assert "Nunca use funções de janela" in prompt
    assert "ROW_NUMBER" in prompt
    assert "maior planned_investment_amount" in prompt
    assert "Não adicione CTE, JOIN, filtro por uf" in prompt
    assert "ILIKE '%Icap%' para Icapuí" in prompt
    assert "project_id exatamente" in prompt


def test_synthesis_prompt_hides_false_limit_disclaimer() -> None:
    prompt = build_synthesis_prompt(
        SynthesisRequest(
            question="Quantos contratos existem?",
            semantic_context="Gold pública do Ceará",
            approved_sql="SELECT COUNT(*) FROM gold.vw_project_contract_current",
            result=LimitedResult(("total",), ((189,),), truncated=False),
        )
    )

    assert "Se truncated for false, não mencione limitação" in prompt


class FakeModels:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def generate_content(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        return self.responses.pop(0)


def test_gemini_adapter_uses_injected_client_without_network() -> None:
    models = FakeModels(
        [
            SimpleNamespace(
                text=json.dumps(
                    {
                        "answerability": "respondible",
                        "sql": (
                            "SELECT count(DISTINCT project_id) "
                            "FROM gold.vw_market_overview_current"
                        ),
                        "reason": "contagem de projetos",
                    }
                )
            ),
            SimpleNamespace(text=json.dumps({"answer": "Há 2 obras."})),
        ]
    )
    client = SimpleNamespace(models=models)
    provider = GeminiProvider(api_key=None, client=client)
    request = SQLGenerationRequest(
        question="Quantas obras existem?",
        semantic_context="VIEW gold.vw_market_overview_current | project_id",
    )

    proposal = provider.generate_sql(request)
    synthesis = provider.synthesize(
        SynthesisRequest(
            question=request.question,
            semantic_context=request.semantic_context,
            approved_sql=proposal.sql or "",
            result=LimitedResult(("project_count",), ((2,),)),
        )
    )

    assert proposal.sql is not None
    assert synthesis.answer == "Há 2 obras."
    assert len(models.calls) == 2
    assert all("GEMINI_API_KEY" not in str(call) for call in models.calls)
    assert all("ingestion_id" not in str(call) for call in models.calls)
    assert models.calls[0]["model"] == "gemini-3.5-flash-lite"


def test_gemini_adapter_rejects_non_structured_response() -> None:
    models = FakeModels([SimpleNamespace(text="texto livre")])
    provider = GeminiProvider(api_key=None, client=SimpleNamespace(models=models))

    with pytest.raises(ProviderResponseError):
        provider.generate_sql(
            SQLGenerationRequest(question="Quantas obras?", semantic_context="Gold pública")
        )


def test_gemini_classifies_model_access_404_as_configuration_error() -> None:
    class ErrorModels:
        def generate_content(self, **kwargs: object) -> object:
            raise RuntimeError("404 NOT_FOUND")

    provider = GeminiProvider(
        api_key=None,
        client=SimpleNamespace(models=ErrorModels()),
    )

    with pytest.raises(ProviderConfigurationError):
        provider.generate_sql(
            SQLGenerationRequest(question="Quantas obras?", semantic_context="Gold pública")
        )


def test_gemini_keeps_transport_failures_as_provider_unavailable() -> None:
    class ErrorModels:
        def generate_content(self, **kwargs: object) -> object:
            raise RuntimeError("connection reset")

    provider = GeminiProvider(
        api_key=None,
        client=SimpleNamespace(models=ErrorModels()),
    )

    with pytest.raises(ProviderUnavailableError):
        provider.generate_sql(
            SQLGenerationRequest(question="Quantas obras?", semantic_context="Gold pública")
        )
