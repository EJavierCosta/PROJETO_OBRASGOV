from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

from .obrasgov import Page, RepeatedPageError
from .resources import PAGINATED_RESOURCES as _PAGINATED_RESOURCES
from .resources import RESOURCE_REGISTRY, RESOURCE_REGISTRY_BY_NAME, SOURCE_UPDATE_RESOURCE

PAGINATED_RESOURCES = _PAGINATED_RESOURCES
LOGGER = logging.getLogger(__name__)


class IngestionRunError(RuntimeError):
    """A execução foi auditada como falha e não foi publicada."""


class ReconciliationError(IngestionRunError):
    """As páginas recebidas não correspondem ao snapshot informado pela API."""


class SourceUpdatedAtChanged(IngestionRunError):
    """A fonte mudou enquanto a carga nacional era coletada."""


class SnapshotRepository(Protocol):
    def find_succeeded_snapshot(
        self,
        *,
        source_updated_at: datetime,
        scope_hash: str,
    ) -> UUID | None: ...

    def create_run(
        self,
        *,
        ingestion_id: UUID,
        started_at: datetime,
        source_updated_at: datetime | None,
        base_url: str,
        query_scope: Mapping[str, Any],
        scope_hash: str,
        force_requested: bool,
    ) -> None: ...

    def set_source_updated_at(
        self,
        *,
        ingestion_id: UUID,
        source_updated_at: datetime,
    ) -> None: ...

    def start_resource(self, *, ingestion_id: UUID, resource_name: str, endpoint: str) -> None: ...

    def persist_page_and_records(
        self,
        *,
        ingestion_id: UUID,
        resource_name: str,
        page: Page,
        requested_page_size: int,
        records: Sequence[Mapping[str, Any]],
        fetched_at: datetime,
    ) -> None: ...

    def mark_resource_succeeded(
        self,
        *,
        ingestion_id: UUID,
        resource_name: str,
        pages_received: int,
        items_received: int,
    ) -> None: ...

    def mark_resource_failed(self, *, ingestion_id: UUID, resource_name: str) -> None: ...

    def finish_run_succeeded(self, *, ingestion_id: UUID, finished_at: datetime) -> None: ...

    def finish_run_skipped(self, *, ingestion_id: UUID, finished_at: datetime) -> None: ...

    def finish_run_failed(
        self,
        *,
        ingestion_id: UUID,
        finished_at: datetime,
        error_message: str,
    ) -> None: ...


class ObrasgovSource(Protocol):
    def source_updated_at(self) -> datetime: ...

    def source_update_payload(self) -> Mapping[str, Any]: ...

    def fetch_page(self, endpoint: str, *, page_number: int, page_size: int) -> Page: ...


@dataclass(frozen=True)
class IngestionResult:
    ingestion_id: UUID
    source_updated_at: datetime
    status: str


def snapshot_scope(*, page_size: int) -> dict[str, Any]:
    return {
        "resources": [resource.name for resource in RESOURCE_REGISTRY],
        "filters": {},
        "page_size": page_size,
    }


def scope_hash(scope: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        scope,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class IngestionPipeline:
    def __init__(
        self,
        *,
        client: ObrasgovSource,
        repository: SnapshotRepository,
        base_url: str,
        page_size: int,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._client = client
        self._repository = repository
        self._base_url = base_url
        self._page_size = page_size
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory

    def run(self, *, force: bool = False) -> IngestionResult:
        started_at = self._clock()
        query_scope = snapshot_scope(page_size=self._page_size)
        current_scope_hash = scope_hash(query_scope)
        ingestion_id = self._id_factory()
        self._repository.create_run(
            ingestion_id=ingestion_id,
            started_at=started_at,
            source_updated_at=None,
            base_url=self._base_url,
            query_scope=query_scope,
            scope_hash=current_scope_hash,
            force_requested=force,
        )

        active_resource: str | None = None
        try:
            source_update_payload = self._source_update_payload()
            source_updated_at = self._source_updated_at(source_update_payload)
            LOGGER.info("source_updated_at=%s", source_updated_at.isoformat())
            self._repository.set_source_updated_at(
                ingestion_id=ingestion_id,
                source_updated_at=source_updated_at,
            )

            existing_run = self._repository.find_succeeded_snapshot(
                source_updated_at=source_updated_at,
                scope_hash=current_scope_hash,
            )
            if existing_run is not None and not force:
                self._repository.finish_run_skipped(
                    ingestion_id=ingestion_id,
                    finished_at=self._clock(),
                )
                return IngestionResult(
                    ingestion_id=existing_run,
                    source_updated_at=source_updated_at,
                    status="skipped",
                )

            for resource in RESOURCE_REGISTRY:
                active_resource = resource.name
                LOGGER.info("iniciando recurso=%s", resource.name)
                if resource.name == SOURCE_UPDATE_RESOURCE:
                    self._record_source_update(
                        ingestion_id,
                        source_updated_at,
                        source_update_payload,
                    )
                else:
                    self._load_resource(ingestion_id, resource.name)
                active_resource = None
                LOGGER.info("recurso concluído=%s", resource.name)

            source_updated_at_after = self._client.source_updated_at()
            if source_updated_at_after != source_updated_at:
                raise SourceUpdatedAtChanged(
                    "source_updated_at mudou durante a paginação: "
                    f"{source_updated_at.isoformat()} -> {source_updated_at_after.isoformat()}."
                )

            self._repository.finish_run_succeeded(
                ingestion_id=ingestion_id,
                finished_at=self._clock(),
            )
        except Exception as error:
            if active_resource is not None:
                self._repository.mark_resource_failed(
                    ingestion_id=ingestion_id,
                    resource_name=active_resource,
                )
            self._repository.finish_run_failed(
                ingestion_id=ingestion_id,
                finished_at=self._clock(),
                error_message=str(error),
            )
            if isinstance(error, IngestionRunError | RepeatedPageError):
                raise
            raise IngestionRunError(f"Falha na ingestão: {error}") from error

        return IngestionResult(
            ingestion_id=ingestion_id,
            source_updated_at=source_updated_at,
            status="succeeded",
        )

    def _source_update_payload(self) -> Mapping[str, Any]:
        payload_method = getattr(self._client, "source_update_payload", None)
        if callable(payload_method):
            return payload_method()
        source_updated_at = self._client.source_updated_at()
        return {"data_ultima_atualizacao": source_updated_at.isoformat()}

    @staticmethod
    def _source_updated_at(payload: Mapping[str, Any]) -> datetime:
        value = payload.get("data_ultima_atualizacao")
        if not isinstance(value, str) or not value.strip() or "T" not in value:
            raise IngestionRunError(
                "Resposta de data-atualizacao sem data_ultima_atualizacao válida."
            )
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise IngestionRunError(
                "data_ultima_atualizacao não possui timestamp ISO-8601 válido."
            ) from error
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    def _record_source_update(
        self,
        ingestion_id: UUID,
        source_updated_at: datetime,
        payload: Mapping[str, Any],
    ) -> None:
        source_update = RESOURCE_REGISTRY_BY_NAME[SOURCE_UPDATE_RESOURCE]
        self._repository.start_resource(
            ingestion_id=ingestion_id,
            resource_name=SOURCE_UPDATE_RESOURCE,
            endpoint=source_update.endpoint,
        )
        page = Page(
            page_number=1,
            total_pages=1,
            total_items=1,
            data=(dict(payload),),
            page_size=1,
        )
        self._repository.persist_page_and_records(
            ingestion_id=ingestion_id,
            resource_name=SOURCE_UPDATE_RESOURCE,
            page=page,
            requested_page_size=1,
            records=(payload,),
            fetched_at=self._clock(),
        )
        self._repository.mark_resource_succeeded(
            ingestion_id=ingestion_id,
            resource_name=SOURCE_UPDATE_RESOURCE,
            pages_received=1,
            items_received=1,
        )

    def _load_resource(self, ingestion_id: UUID, resource_name: str) -> None:
        resource = RESOURCE_REGISTRY_BY_NAME[resource_name]
        self._repository.start_resource(
            ingestion_id=ingestion_id,
            resource_name=resource_name,
            endpoint=resource.endpoint,
        )

        first_page = self._client.fetch_page(
            resource.endpoint,
            page_number=1,
            page_size=self._page_size,
        )
        LOGGER.info(
            "primeira página recebida recurso=%s páginas=%s itens=%s",
            resource_name,
            first_page.total_pages,
            first_page.total_items,
        )
        expected_pages = first_page.total_pages
        expected_items = first_page.total_items
        pages_received = 0
        items_received = 0
        seen_pages: set[int] = set()

        def persist(page: Page) -> None:
            nonlocal pages_received, items_received
            self._validate_page(
                page,
                resource_name=resource_name,
                expected_pages=expected_pages,
                expected_items=expected_items,
                seen_pages=seen_pages,
            )
            self._repository.persist_page_and_records(
                ingestion_id=ingestion_id,
                resource_name=resource_name,
                page=page,
                requested_page_size=self._page_size,
                records=page.data,
                fetched_at=self._clock(),
            )
            LOGGER.info(
                "página persistida recurso=%s página=%s itens=%s",
                resource_name,
                page.page_number,
                page.returned_item_count,
            )
            pages_received += 1
            items_received += page.returned_item_count

        if expected_pages > 0:
            persist(first_page)
            for page_number in range(2, expected_pages + 1):
                persist(
                    self._client.fetch_page(
                        resource.endpoint,
                        page_number=page_number,
                        page_size=self._page_size,
                    )
                )

        expected_page_fetches = expected_pages
        if pages_received != expected_page_fetches or items_received != expected_items:
            raise ReconciliationError(
                f"Reconciliação inválida para {resource_name}: "
                f"páginas={pages_received}/{expected_page_fetches}, "
                f"itens={items_received}/{expected_items}."
            )

        self._repository.mark_resource_succeeded(
            ingestion_id=ingestion_id,
            resource_name=resource_name,
            pages_received=pages_received,
            items_received=items_received,
        )

    @staticmethod
    def _validate_page(
        page: Page,
        *,
        resource_name: str,
        expected_pages: int,
        expected_items: int,
        seen_pages: set[int],
    ) -> None:
        if page.page_number in seen_pages:
            raise RepeatedPageError(
                f"Página {page.page_number} repetida durante a carga de {resource_name}."
            )
        if page.total_pages != expected_pages or page.total_items != expected_items:
            raise ReconciliationError(
                f"Totais variaram entre páginas de {resource_name}."
            )
        seen_pages.add(page.page_number)
