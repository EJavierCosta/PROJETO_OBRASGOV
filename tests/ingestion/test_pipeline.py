from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from obrasgov_ingestion.obrasgov import Page, RepeatedPageError
from obrasgov_ingestion.pipeline import (
    IngestionPipeline,
    IngestionRunError,
    SourceUpdatedAtChanged,
    scope_hash,
)

RUN_ID = UUID("00000000-0000-0000-0000-000000000001")
EXISTING_RUN_ID = UUID("00000000-0000-0000-0000-000000000002")
SOURCE_UPDATED_AT = datetime(2026, 8, 21, 12, tzinfo=UTC)
SOURCE_UPDATED_AT_NEXT = datetime(2026, 8, 21, 13, tzinfo=UTC)


class FakeRepository:
    def __init__(self, existing_run: UUID | None = None) -> None:
        self.existing_run = existing_run
        self.created_runs: list[dict[str, Any]] = []
        self.started_resources: list[str] = []
        self.persisted_pages: list[dict[str, Any]] = []
        self.persisted_records: list[dict[str, Any]] = []
        self.succeeded_resources: list[str] = []
        self.failed_resources: list[str] = []
        self.finished_runs: list[tuple[str, str | None]] = []

    def find_succeeded_snapshot(
        self,
        *,
        source_updated_at: datetime,
        scope_hash: str,
    ) -> UUID | None:
        return self.existing_run

    def create_run(self, **kwargs: Any) -> None:
        self.created_runs.append(kwargs)

    def set_source_updated_at(self, **_: Any) -> None:
        return None

    def start_resource(self, *, ingestion_id: UUID, resource_name: str, endpoint: str) -> None:
        self.started_resources.append(resource_name)

    def persist_page_and_records(
        self,
        *,
        ingestion_id: UUID,
        resource_name: str,
        page: Page,
        requested_page_size: int,
        records: Sequence[Mapping[str, Any]],
        fetched_at: datetime,
    ) -> None:
        self.persisted_pages.append(
            {
                "resource_name": resource_name,
                "page_number": page.page_number,
                "requested_page_size": requested_page_size,
                "item_count": page.returned_item_count,
            }
        )
        self.persisted_records.extend(dict(record) for record in records)

    def mark_resource_succeeded(
        self,
        *,
        ingestion_id: UUID,
        resource_name: str,
        pages_received: int,
        items_received: int,
    ) -> None:
        self.succeeded_resources.append(resource_name)

    def mark_resource_failed(self, *, ingestion_id: UUID, resource_name: str) -> None:
        self.failed_resources.append(resource_name)

    def finish_run_succeeded(self, *, ingestion_id: UUID, finished_at: datetime) -> None:
        self.finished_runs.append(("succeeded", None))

    def finish_run_skipped(self, *, ingestion_id: UUID, finished_at: datetime) -> None:
        self.finished_runs.append(("skipped", None))

    def finish_run_failed(
        self,
        *,
        ingestion_id: UUID,
        finished_at: datetime,
        error_message: str,
    ) -> None:
        self.finished_runs.append(("failed", error_message))


class FakeClient:
    def __init__(
        self,
        *,
        source_updates: list[datetime],
        pages: Mapping[tuple[str, int], Page | Exception],
    ) -> None:
        self._source_updates = iter(source_updates)
        self._pages = pages
        self.source_requests = 0
        self.page_requests: list[tuple[str, int, int]] = []

    def source_updated_at(self) -> datetime:
        self.source_requests += 1
        return next(self._source_updates)

    def source_update_payload(self) -> Mapping[str, Any]:
        return {"data_ultima_atualizacao": self.source_updated_at().isoformat()}

    def fetch_page(self, endpoint: str, *, page_number: int, page_size: int) -> Page:
        self.page_requests.append((endpoint, page_number, page_size))
        result = self._pages[(endpoint, page_number)]
        if isinstance(result, Exception):
            raise result
        return result


def _page(
    page_number: int,
    total_pages: int,
    total_items: int,
    *records: dict[str, Any],
) -> Page:
    return Page(
        page_number=page_number,
        total_pages=total_pages,
        total_items=total_items,
        data=tuple(records),
    )


def _pipeline(client: FakeClient, repository: FakeRepository) -> IngestionPipeline:
    return IngestionPipeline(
        client=client,
        repository=repository,
        base_url="https://example.test/obras",
        page_size=2,
        clock=lambda: SOURCE_UPDATED_AT,
        id_factory=lambda: RUN_ID,
    )


def _successful_pages() -> dict[tuple[str, int], Page]:
    return {
        ("projeto-investimento", 1): _page(1, 1, 1, {"id": "projeto-1"}),
        ("geometria", 1): _page(1, 1, 1, {"id": "geometria-1"}),
    }


def test_paginated_full_load_reconciles_pages_items_and_records() -> None:
    client = FakeClient(
        source_updates=[SOURCE_UPDATED_AT, SOURCE_UPDATED_AT],
        pages={
            ("projeto-investimento", 1): _page(1, 2, 3, {"id": "p1"}, {"id": "p2"}),
            ("projeto-investimento", 2): _page(2, 2, 3, {"id": "p3"}),
            ("geometria", 1): _page(1, 1, 1, {"id": "g1"}),
        },
    )
    repository = FakeRepository()

    result = _pipeline(client, repository).run()

    assert result.status == "succeeded"
    assert client.page_requests == [
        ("projeto-investimento", 1, 2),
        ("projeto-investimento", 2, 2),
        ("geometria", 1, 2),
    ]
    assert [
        page["page_number"]
        for page in repository.persisted_pages
        if page["resource_name"] == "projeto-investimento"
    ] == [1, 2]
    assert len(repository.persisted_records) == 5
    assert client.source_requests == 2
    assert repository.finished_runs == [("succeeded", None)]


def test_failure_is_auditable_and_is_not_published() -> None:
    client = FakeClient(
        source_updates=[SOURCE_UPDATED_AT],
        pages={
            ("projeto-investimento", 1): RuntimeError("API indisponível"),
        },
    )
    repository = FakeRepository()

    with pytest.raises(IngestionRunError, match="API indisponível"):
        _pipeline(client, repository).run()

    assert repository.failed_resources == ["projeto-investimento"]
    assert repository.finished_runs == [("failed", "API indisponível")]
    assert "succeeded" not in [status for status, _ in repository.finished_runs]


def test_source_update_change_marks_run_failed() -> None:
    client = FakeClient(
        source_updates=[SOURCE_UPDATED_AT, SOURCE_UPDATED_AT_NEXT],
        pages=_successful_pages(),
    )
    repository = FakeRepository()

    with pytest.raises(SourceUpdatedAtChanged, match="source_updated_at mudou"):
        _pipeline(client, repository).run()

    assert repository.finished_runs[0][0] == "failed"
    assert "succeeded" not in [status for status, _ in repository.finished_runs]


def test_existing_successful_snapshot_is_skipped_without_fetching_pages() -> None:
    client = FakeClient(source_updates=[SOURCE_UPDATED_AT], pages={})
    repository = FakeRepository(existing_run=EXISTING_RUN_ID)

    result = _pipeline(client, repository).run()

    assert result.status == "skipped"
    assert result.ingestion_id == EXISTING_RUN_ID
    assert repository.created_runs[0]["source_updated_at"] is None
    assert repository.finished_runs == [("skipped", None)]
    assert not client.page_requests
    assert client.source_requests == 1


def test_force_creates_another_snapshot_for_same_logical_identity() -> None:
    client = FakeClient(
        source_updates=[SOURCE_UPDATED_AT, SOURCE_UPDATED_AT],
        pages=_successful_pages(),
    )
    repository = FakeRepository(existing_run=EXISTING_RUN_ID)

    result = _pipeline(client, repository).run(force=True)

    assert result.status == "succeeded"
    assert result.ingestion_id == RUN_ID
    assert len(repository.created_runs) == 1
    assert repository.created_runs[0]["force_requested"] is True


def test_duplicate_page_fails_before_duplicate_records_are_published() -> None:
    client = FakeClient(
        source_updates=[SOURCE_UPDATED_AT],
        pages={
            ("projeto-investimento", 1): _page(1, 2, 2, {"id": "p1"}),
            ("projeto-investimento", 2): _page(1, 2, 2, {"id": "p2"}),
        },
    )
    repository = FakeRepository()

    with pytest.raises(RepeatedPageError, match="Página 1 repetida"):
        _pipeline(client, repository).run()

    project_records = [
        record
        for record in repository.persisted_records
        if str(record.get("id", "")).startswith("p")
    ]
    assert project_records == [{"id": "p1"}]
    assert repository.finished_runs[0][0] == "failed"


def test_scope_hash_is_deterministic_for_equivalent_json() -> None:
    assert scope_hash({"filters": {}, "resources": ["a", "b"], "page_size": 2}) == scope_hash(
        {"resources": ["a", "b"], "filters": {}, "page_size": 2}
    )
