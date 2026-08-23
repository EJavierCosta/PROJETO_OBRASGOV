"""Provider determinístico para testes locais, sem rede ou runtime externo."""

from __future__ import annotations

from collections.abc import Sequence

from ..contracts import (
    Answerability,
    SQLGenerationRequest,
    SQLProposal,
    SynthesisEnvelope,
    SynthesisRequest,
)


class FakeProvider:
    """Provider controlável que registra chamadas sem registrar prompts em logs."""

    name = "fake"

    def __init__(
        self,
        *,
        proposal: SQLProposal | None = None,
        synthesis: SynthesisEnvelope | None = None,
        sql: str | None = None,
        answer: str = "Resposta determinística baseada no resultado Gold.",
        answerability: Answerability = Answerability.RESPONDIBLE,
        sql_responses: Sequence[SQLProposal] = (),
        synthesis_responses: Sequence[SynthesisEnvelope] = (),
    ) -> None:
        if proposal is None:
            default_sql = (
                "SELECT count(DISTINCT project_id) AS project_count "
                "FROM gold.vw_market_overview_current"
            )
            proposal = SQLProposal(
                answerability=answerability,
                sql=sql
                or (
                    default_sql
                    if answerability is Answerability.RESPONDIBLE
                    else None
                ),
            )
        self._proposal = proposal
        self._synthesis = synthesis or SynthesisEnvelope(answer)
        self._sql_responses = list(sql_responses)
        self._synthesis_responses = list(synthesis_responses)
        self.sql_requests: list[SQLGenerationRequest] = []
        self.synthesis_requests: list[SynthesisRequest] = []

    def generate_sql(self, request: SQLGenerationRequest) -> SQLProposal:
        self.sql_requests.append(request)
        if self._sql_responses:
            return self._sql_responses.pop(0)
        return self._proposal

    def synthesize(self, request: SynthesisRequest) -> SynthesisEnvelope:
        self.synthesis_requests.append(request)
        if self._synthesis_responses:
            return self._synthesis_responses.pop(0)
        return self._synthesis


__all__ = ["FakeProvider"]
