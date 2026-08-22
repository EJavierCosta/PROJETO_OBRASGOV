from __future__ import annotations

import httpx
import pytest
from obrasgov_ingestion.obrasgov import ObrasgovClient, ObrasgovError, RepeatedPageError


def _page_body(*, page_number: int, total_pages: int, total_items: int, data: list[dict]) -> dict:
    return {
        "page_number": page_number,
        "page_size": 200,
        "total_pages": total_pages,
        "total_items": total_items,
        "data": data,
    }


def test_retries_only_transient_http_failure_and_preserves_pagination_parameters() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(503, request=request)
        return httpx.Response(
            200,
            json=_page_body(
                page_number=1,
                total_pages=1,
                total_items=1,
                data=[{"id_projeto_investimento": "1"}],
            ),
            request=request,
        )

    with ObrasgovClient(
        base_url="https://example.test/obras",
        timeout_seconds=2,
        max_retries=1,
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    ) as client:
        page = client.fetch_page("projeto-investimento", page_number=1, page_size=200)

    assert page.returned_item_count == 1
    assert len(requests) == 2
    assert requests[0].url.path == "/obras/projeto-investimento"
    assert requests[1].url.params["pagina"] == "1"
    assert requests[1].url.params["tamanho_da_pagina"] == "200"


def test_rejects_response_for_a_previously_seen_page() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_page_body(
                page_number=1,
                total_pages=2,
                total_items=2,
                data=[{"id_projeto_investimento": "1"}],
            ),
            request=request,
        )

    with ObrasgovClient(
        base_url="https://example.test/obras",
        timeout_seconds=2,
        max_retries=0,
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(RepeatedPageError, match="page_number=1"):
            client.fetch_page("projeto-investimento", page_number=2, page_size=1)


def test_does_not_retry_non_transient_http_failure() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(400, request=request)

    with ObrasgovClient(
        base_url="https://example.test/obras",
        timeout_seconds=2,
        max_retries=3,
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    ) as client:
        with pytest.raises(ObrasgovError, match="HTTP 400"):
            client.fetch_page("projeto-investimento", page_number=1, page_size=1)

    assert len(requests) == 1
