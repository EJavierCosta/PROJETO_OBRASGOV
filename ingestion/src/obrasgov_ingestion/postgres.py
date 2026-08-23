from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from .obrasgov import Page
from .resources import RESOURCE_REGISTRY

RAW_TABLES = {
    resource.name: ("bronze", resource.raw_table) for resource in RESOURCE_REGISTRY
}


class PersistenceError(RuntimeError):
    """Erro ao registrar uma execução no PostgreSQL."""


def payload_hash(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class PostgresRepository:
    def __init__(self, connection: psycopg.Connection[Any]) -> None:
        self._connection = connection

    @classmethod
    def connect(cls, database_url: str) -> PostgresRepository:
        return cls(psycopg.connect(database_url, autocommit=True))

    def close(self) -> None:
        self._connection.close()

    def find_succeeded_snapshot(
        self,
        *,
        source_updated_at: datetime,
        scope_hash: str,
    ) -> UUID | None:
        query = """
            SELECT ingestion_id
            FROM bronze.ingestion_run
            WHERE status = 'succeeded'
              AND source_updated_at = %s
              AND scope_hash = %s
            ORDER BY finished_at DESC
            LIMIT 1
        """
        with self._connection.cursor() as cursor:
            cursor.execute(query, (source_updated_at, scope_hash))
            row = cursor.fetchone()
        return row[0] if row else None

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
    ) -> None:
        self._write(
            """
            INSERT INTO bronze.ingestion_run (
                ingestion_id, started_at, status, source_updated_at, base_url,
                query_scope, scope_hash, force_requested
            )
            VALUES (%s, %s, 'running', %s, %s, %s, %s, %s)
            """,
            (
                ingestion_id,
                started_at,
                source_updated_at,
                base_url,
                Jsonb(dict(query_scope)),
                scope_hash,
                force_requested,
            ),
        )

    def set_source_updated_at(
        self,
        *,
        ingestion_id: UUID,
        source_updated_at: datetime,
    ) -> None:
        rowcount = self._write(
            """
            UPDATE bronze.ingestion_run
            SET source_updated_at = %s
            WHERE ingestion_id = %s
              AND status = 'running'
              AND source_updated_at IS NULL
            """,
            (source_updated_at, ingestion_id),
        )
        self._require_one_row(rowcount, "registrar source_updated_at")

    def start_resource(self, *, ingestion_id: UUID, resource_name: str, endpoint: str) -> None:
        self._write(
            """
            INSERT INTO bronze.ingestion_resource (
                ingestion_id, resource_name, endpoint, total_pages, total_items
            )
            VALUES (%s, %s, %s, 0, 0)
            """,
            (ingestion_id, resource_name, endpoint),
        )

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
        with self._connection.transaction():
            with self._connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE bronze.ingestion_resource
                    SET total_pages = %s,
                        total_items = %s
                    WHERE ingestion_id = %s
                      AND resource_name = %s
                      AND status = 'running'
                    """,
                    (page.total_pages, page.total_items, ingestion_id, resource_name),
                )
                self._require_one_row(cursor.rowcount, "atualizar metadados do recurso")

                cursor.execute(
                    """
                    INSERT INTO bronze.ingestion_page (
                        ingestion_id, resource_name, page_number, requested_page_size,
                        returned_page_size, returned_item_count, total_pages, total_items,
                        fetched_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ingestion_id, resource_name, page_number) DO NOTHING
                    """,
                    (
                        ingestion_id,
                        resource_name,
                        page.page_number,
                        requested_page_size,
                        page.page_size or page.returned_item_count,
                        page.returned_item_count,
                        page.total_pages,
                        page.total_items,
                        fetched_at,
                    ),
                )

                if records:
                    cursor.executemany(
                        self._raw_insert_statement(resource_name),
                        [
                            (
                                ingestion_id,
                                page.page_number,
                                requested_page_size,
                                record_index,
                                Jsonb(dict(record)),
                                payload_hash(record),
                                fetched_at,
                            )
                            for record_index, record in enumerate(records, start=1)
                        ],
                    )

    def mark_resource_succeeded(
        self,
        *,
        ingestion_id: UUID,
        resource_name: str,
        pages_received: int,
        items_received: int,
    ) -> None:
        rowcount = self._write(
            """
            UPDATE bronze.ingestion_resource
            SET pages_received = %s,
                items_received = %s,
                status = 'succeeded'
            WHERE ingestion_id = %s
              AND resource_name = %s
              AND status = 'running'
            """,
            (pages_received, items_received, ingestion_id, resource_name),
        )
        self._require_one_row(rowcount, "publicar recurso")

    def mark_resource_failed(self, *, ingestion_id: UUID, resource_name: str) -> None:
        self._write(
            """
            UPDATE bronze.ingestion_resource AS resource
            SET pages_received = (
                    SELECT COUNT(*)
                    FROM bronze.ingestion_page AS page
                    WHERE page.ingestion_id = resource.ingestion_id
                      AND page.resource_name = resource.resource_name
                ),
                items_received = COALESCE((
                    SELECT SUM(page.returned_item_count)
                    FROM bronze.ingestion_page AS page
                    WHERE page.ingestion_id = resource.ingestion_id
                      AND page.resource_name = resource.resource_name
                ), 0),
                status = 'failed'
            WHERE resource.ingestion_id = %s
              AND resource.resource_name = %s
              AND resource.status = 'running'
            """,
            (ingestion_id, resource_name),
        )

    def finish_run_succeeded(self, *, ingestion_id: UUID, finished_at: datetime) -> None:
        rowcount = self._write(
            """
            UPDATE bronze.ingestion_run AS run
            SET status = 'succeeded',
                finished_at = %s,
                error_message = NULL
            WHERE run.ingestion_id = %s
              AND run.status = 'running'
              AND (
                    SELECT COUNT(*)
                    FROM bronze.ingestion_resource AS resource
                    WHERE resource.ingestion_id = run.ingestion_id
                ) = jsonb_array_length(run.query_scope -> 'resources')
              AND NOT EXISTS (
                    SELECT 1
                    FROM jsonb_array_elements_text(run.query_scope -> 'resources')
                        AS expected(resource_name)
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM bronze.ingestion_resource AS resource
                        WHERE resource.ingestion_id = run.ingestion_id
                          AND resource.resource_name = expected.resource_name
                          AND resource.status = 'succeeded'
                    )
                )
              AND NOT EXISTS (
                    SELECT 1
                    FROM bronze.ingestion_resource AS resource
                    WHERE resource.ingestion_id = run.ingestion_id
                      AND resource.status <> 'succeeded'
                )
            """,
            (finished_at, ingestion_id),
        )
        self._require_one_row(rowcount, "publicar execução")

    def finish_run_skipped(self, *, ingestion_id: UUID, finished_at: datetime) -> None:
        rowcount = self._write(
            """
            UPDATE bronze.ingestion_run
            SET status = 'skipped',
                finished_at = %s,
                error_message = NULL
            WHERE ingestion_id = %s
              AND status = 'running'
            """,
            (finished_at, ingestion_id),
        )
        self._require_one_row(rowcount, "registrar execução pulada")

    def finish_run_failed(
        self,
        *,
        ingestion_id: UUID,
        finished_at: datetime,
        error_message: str,
    ) -> None:
        self._write(
            """
            UPDATE bronze.ingestion_run
            SET status = 'failed',
                finished_at = %s,
                error_message = %s
            WHERE ingestion_id = %s
              AND status = 'running'
            """,
            (finished_at, error_message, ingestion_id),
        )

    def _write(self, statement: str, parameters: tuple[object, ...]) -> int:
        with self._connection.transaction():
            with self._connection.cursor() as cursor:
                cursor.execute(statement, parameters)
                return cursor.rowcount

    @staticmethod
    def _raw_insert_statement(resource_name: str) -> sql.Composed:
        try:
            schema_name, table_name = RAW_TABLES[resource_name]
        except KeyError as error:
            raise PersistenceError(f"Recurso sem tabela raw: {resource_name}.") from error

        return sql.SQL(
            """
            INSERT INTO {}.{} (
                ingestion_id, page_number, page_size, record_index, payload, record_hash, fetched_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ingestion_id, page_number, record_index) DO NOTHING
            """
        ).format(sql.Identifier(schema_name), sql.Identifier(table_name))

    @staticmethod
    def _require_one_row(rowcount: int, action: str) -> None:
        if rowcount != 1:
            raise PersistenceError(f"Não foi possível {action}.")
