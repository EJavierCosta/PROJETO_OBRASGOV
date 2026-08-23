from __future__ import annotations

from pathlib import Path

import pytest

from frontend import gold


class FakeCursor:
    def __init__(self, rows: list[tuple[object, ...]], columns: list[str] | None = None) -> None:
        self.rows = rows
        self.description = [(column,) for column in (columns or ["project_id"])]
        self.executed: list[str] = []
        self.closed = False
        self.raise_on_query = False

    def execute(self, query: str) -> None:
        self.executed.append(query)
        if self.raise_on_query and query.startswith("SELECT"):
            error = RuntimeError("statement timeout")
            error.sqlstate = "57014"  # type: ignore[attr-defined]
            raise error

    def fetchmany(self, size: int) -> list[tuple[object, ...]]:
        assert size > len(self.rows) - 1
        return self.rows

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self.fake_cursor = cursor
        self.rollback_count = 0
        self.close_count = 0

    def cursor(self) -> FakeCursor:
        return self.fake_cursor

    def rollback(self) -> None:
        self.rollback_count += 1

    def close(self) -> None:
        self.close_count += 1


def _factory(connection: FakeConnection):
    return lambda: connection


def _query() -> str:
    return "SELECT project_id FROM gold.vw_market_overview_current"


def test_executor_uses_read_only_transaction_fixed_search_path_and_rollback() -> None:
    cursor = FakeCursor([("p-1",), ("p-2",)])
    connection = FakeConnection(cursor)

    result = gold.execute_chat_query(
        _query(),
        limits=gold.ChatQueryLimits(max_rows=1, max_columns=2, max_cells=2, max_bytes=100),
        connection_factory=_factory(connection),
    )

    assert result.rows == (("p-1",),)
    assert result.truncated is True
    assert cursor.executed[:3] == [
        "SET TRANSACTION READ ONLY",
        "SET LOCAL search_path TO gold, pg_catalog",
        "SET LOCAL statement_timeout = 5000",
    ]
    assert cursor.executed[-1] == _query()
    assert connection.rollback_count == 1
    assert connection.close_count == 1
    assert cursor.closed is True


def test_executor_limits_columns_cells_and_bytes() -> None:
    too_many_columns = FakeConnection(FakeCursor([(1, 2)], columns=["a", "b"]))
    with pytest.raises(gold.GoldResultLimitError):
        gold.execute_chat_query(
            _query(),
            limits=gold.ChatQueryLimits(max_columns=1),
            connection_factory=_factory(too_many_columns),
        )
    assert too_many_columns.rollback_count == 1

    cell_limited = FakeConnection(FakeCursor([("a",), ("b",)]))
    result = gold.execute_chat_query(
        _query(),
        limits=gold.ChatQueryLimits(max_rows=10, max_cells=1, max_bytes=100),
        connection_factory=_factory(cell_limited),
    )
    assert result.rows == (("a",),)
    assert result.truncated is True

    byte_limited = FakeConnection(FakeCursor([("large",), ("later",)]))
    result = gold.execute_chat_query(
        _query(),
        limits=gold.ChatQueryLimits(max_rows=10, max_cells=10, max_bytes=4),
        connection_factory=_factory(byte_limited),
    )
    assert result.rows == ()
    assert result.truncated is True


def test_timeout_rolls_back_and_exposes_sanitized_error() -> None:
    cursor = FakeCursor([])
    cursor.raise_on_query = True
    connection = FakeConnection(cursor)

    with pytest.raises(gold.GoldTimeoutError, match="tempo limite"):
        gold.execute_chat_query(_query(), connection_factory=_factory(connection))

    assert connection.rollback_count == 1
    assert connection.close_count == 1


def test_invalid_sql_never_opens_connection() -> None:
    opened = False

    def factory() -> FakeConnection:
        nonlocal opened
        opened = True
        return FakeConnection(FakeCursor([]))

    with pytest.raises(ValueError):
        gold.execute_chat_query(
            "SELECT * FROM gold.vw_market_overview_current",
            connection_factory=factory,
        )

    assert opened is False


def test_metadata_uses_static_sql_without_ingestion_id() -> None:
    cursor = FakeCursor(
        [("2026-08-21", "2026-08-22")],
        columns=["source_updated_at", "ingested_at"],
    )
    connection = FakeConnection(cursor)

    metadata = gold.load_chat_snapshot_metadata(
        limits=gold.ChatQueryLimits(max_rows=1, max_columns=2, max_cells=2, max_bytes=100),
        connection_factory=_factory(connection),
    )

    assert metadata == gold.ChatSnapshotMetadata("2026-08-21", "2026-08-22")
    assert "ingestion_id" not in cursor.executed[-1].lower()
    assert connection.rollback_count == 1


def test_chat_connection_does_not_fallback_to_frontend_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOLD_DATABASE_URL", "postgresql+psycopg://frontend-only")
    monkeypatch.delenv("GOLD_CHAT_DATABASE_URL", raising=False)

    with pytest.raises(gold.GoldConfigurationError):
        gold.execute_chat_query(_query())


def test_compose_uses_a_psycopg_compatible_chat_url() -> None:
    compose = (Path(__file__).parents[2] / "compose.yaml").read_text(encoding="utf-8")

    assert "GOLD_CHAT_DATABASE_URL: postgresql://obrasgov_chat" in compose
    assert "GOLD_CHAT_DATABASE_URL: postgresql+psycopg://" not in compose


def test_bootstrap_declares_dedicated_role_and_exact_business_views() -> None:
    root = Path(__file__).parents[2]
    roles = (root / "infra/postgres/initdb/00_roles.sql").read_text(encoding="utf-8")
    grants = (root / "infra/postgres/initdb/20_grants.sql").read_text(encoding="utf-8")

    assert "CREATE ROLE obrasgov_chat" in roles
    assert "LOGIN" in roles
    assert "REVOKE ALL ON ALL TABLES IN SCHEMA gold FROM obrasgov_chat" in grants
    for view in (
        "vw_market_overview_current",
        "vw_project_investment_current",
        "vw_project_location_current",
        "vw_status_distribution_current",
    ):
        assert view in grants
    assert "vw_snapshot_metadata_current" in grants
    assert "GRANT SELECT (source_updated_at, ingested_at" in grants
    assert "GRANT SELECT ON gold.vw_snapshot_metadata_current TO obrasgov_chat" not in grants
    assert "TEMPORARY" in grants
