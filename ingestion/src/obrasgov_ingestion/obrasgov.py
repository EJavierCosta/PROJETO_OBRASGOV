from __future__ import annotations

import math
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

MAX_PAGE_SIZE = 200
TRANSIENT_STATUS_CODES = frozenset({408, 425, 429, 500, 502, 503, 504})


class ObrasgovError(RuntimeError):
    """Erro ao consultar ou validar a API ObrasGov."""


class RequestFailedError(ObrasgovError):
    """Falha HTTP transitória esgotou as retentativas."""


class ResponseEnvelopeError(ObrasgovError):
    """Resposta JSON não atende ao contrato esperado."""


class RepeatedPageError(ResponseEnvelopeError):
    """A API respondeu uma página diferente da solicitada."""


@dataclass(frozen=True)
class Page:
    page_number: int
    total_pages: int
    total_items: int
    data: tuple[dict[str, Any], ...]
    page_size: int = 0

    @property
    def returned_item_count(self) -> int:
        return len(self.data)


class ObrasgovClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        max_retries: int,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        if not base_url.strip():
            raise ValueError("OBRASGOV_BASE_URL não pode ser vazio.")
        if timeout_seconds <= 0:
            raise ValueError("O timeout deve ser maior que zero.")
        if max_retries < 0:
            raise ValueError("O número de retentativas não pode ser negativo.")

        self._max_retries = max_retries
        self._sleep = sleep or time.sleep
        self._client = httpx.Client(
            base_url=f"{base_url.rstrip('/')}/",
            timeout=httpx.Timeout(timeout_seconds),
            headers={"Accept": "application/json"},
            transport=transport,
        )

    def __enter__(self) -> ObrasgovClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def source_updated_at(self) -> datetime:
        return self._parse_source_updated_at(self.source_update_payload())

    def source_update_payload(self) -> dict[str, Any]:
        return self._request_json("data-atualizacao")

    @staticmethod
    def _parse_source_updated_at(body: Mapping[str, Any]) -> datetime:
        value = body.get("data_ultima_atualizacao")
        if not isinstance(value, str) or not value.strip() or "T" not in value:
            raise ResponseEnvelopeError(
                "Resposta de data-atualizacao sem data_ultima_atualizacao válida."
            )

        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ResponseEnvelopeError(
                "data_ultima_atualizacao não possui timestamp ISO-8601 válido."
            ) from error

        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    def fetch_page(self, endpoint: str, *, page_number: int, page_size: int) -> Page:
        self._validate_page_request(page_number=page_number, page_size=page_size)
        body = self._request_json(
            endpoint,
            params={"pagina": page_number, "tamanho_da_pagina": page_size},
        )
        return self._parse_page(
            body,
            endpoint=endpoint,
            page_number=page_number,
            page_size=page_size,
        )

    def _request_json(
        self,
        endpoint: str,
        params: Mapping[str, int] | None = None,
    ) -> dict[str, Any]:
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.get(endpoint, params=params)
            except (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.RemoteProtocolError,
            ) as error:
                if attempt == self._max_retries:
                    raise RequestFailedError(
                        f"Falha transitória em {endpoint} após {attempt + 1} tentativa(s)."
                    ) from error
                self._sleep(self._retry_delay(attempt))
                continue

            if response.status_code in TRANSIENT_STATUS_CODES:
                if attempt == self._max_retries:
                    raise RequestFailedError(
                        f"API respondeu HTTP {response.status_code} em {endpoint} "
                        f"após {attempt + 1} tentativa(s)."
                    )
                self._sleep(self._retry_delay(attempt))
                continue

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                raise ObrasgovError(
                    f"API respondeu HTTP {response.status_code} em {endpoint}."
                ) from error

            try:
                body = response.json()
            except ValueError as error:
                raise ResponseEnvelopeError(f"API retornou JSON inválido em {endpoint}.") from error

            if not isinstance(body, Mapping):
                raise ResponseEnvelopeError(f"API retornou envelope não-objeto em {endpoint}.")
            return dict(body)

        raise AssertionError("Fluxo de retentativa deveria ter retornado ou lançado erro.")

    @staticmethod
    def _retry_delay(attempt: int) -> float:
        return 0.5 * (2**attempt)

    @staticmethod
    def _validate_page_request(*, page_number: int, page_size: int) -> None:
        if page_number < 1:
            raise ValueError("pagina deve iniciar em 1.")
        if not 1 <= page_size <= MAX_PAGE_SIZE:
            raise ValueError(f"tamanho_da_pagina deve estar entre 1 e {MAX_PAGE_SIZE}.")

    def _parse_page(
        self,
        body: Mapping[str, Any],
        *,
        endpoint: str,
        page_number: int,
        page_size: int,
    ) -> Page:
        data = body.get("data")
        if not isinstance(data, list):
            raise ResponseEnvelopeError(
                f"Envelope paginado inválido em {endpoint}: data deve ser lista."
            )

        returned_page = self._required_int(body, "page_number", endpoint)
        returned_page_size = self._required_int(body, "page_size", endpoint)
        total_pages = self._required_int(body, "total_pages", endpoint)
        total_items = self._required_int(body, "total_items", endpoint)

        if returned_page != page_number:
            raise RepeatedPageError(
                f"API retornou page_number={returned_page} para pagina={page_number} em {endpoint}."
            )
        if returned_page_size < 1 or returned_page_size > MAX_PAGE_SIZE:
            raise ResponseEnvelopeError(f"page_size inválido no envelope de {endpoint}.")
        if total_pages < 0 or total_items < 0:
            raise ResponseEnvelopeError(f"Totais negativos no envelope de {endpoint}.")
        if len(data) > page_size:
            raise ResponseEnvelopeError(
                f"Envelope de {endpoint} retornou mais itens que tamanho_da_pagina."
            )

        expected_total_pages = math.ceil(total_items / page_size)
        if total_pages != expected_total_pages:
            raise ResponseEnvelopeError(
                f"total_pages inconsistente com total_items em {endpoint}."
            )
        if total_pages == 0 and data:
            raise ResponseEnvelopeError(f"Envelope vazio de {endpoint} contém itens.")
        if total_pages > 0 and page_number > total_pages:
            raise ResponseEnvelopeError(f"Página {page_number} excede total_pages em {endpoint}.")
        if total_items > 0 and not data:
            raise ResponseEnvelopeError(f"Página vazia inesperada em {endpoint}.")

        records: list[dict[str, Any]] = []
        for index, item in enumerate(data, start=1):
            if not isinstance(item, Mapping):
                raise ResponseEnvelopeError(f"Item {index} de {endpoint} não é objeto JSON.")
            records.append(dict(item))

        return Page(
            page_number=returned_page,
            total_pages=total_pages,
            total_items=total_items,
            data=tuple(records),
            page_size=returned_page_size,
        )

    @staticmethod
    def _required_int(body: Mapping[str, Any], field: str, endpoint: str) -> int:
        value = body.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ResponseEnvelopeError(f"Envelope de {endpoint} sem {field} inteiro válido.")
        return value
