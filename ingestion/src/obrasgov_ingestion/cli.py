from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass

from .obrasgov import MAX_PAGE_SIZE, ObrasgovClient
from .pipeline import IngestionPipeline
from .postgres import PostgresRepository


@dataclass(frozen=True)
class RuntimeConfig:
    database_url: str
    base_url: str
    page_size: int
    timeout_seconds: float
    max_retries: int
    force: bool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Executa o snapshot Bronze nacional do ObrasGov.")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    parser.add_argument(
        "--base-url",
        default=os.getenv("OBRASGOV_BASE_URL", "https://api-publica.obrasgov.gestao.gov.br/obras"),
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=_environment_int("OBRASGOV_PAGE_SIZE", 200),
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=_environment_float("OBRASGOV_TIMEOUT_SECONDS", 120.0),
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=_environment_int("OBRASGOV_MAX_RETRIES", 3),
    )
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)

    try:
        config = _runtime_config(arguments)
        repository = PostgresRepository.connect(config.database_url)
        try:
            with ObrasgovClient(
                base_url=config.base_url,
                timeout_seconds=config.timeout_seconds,
                max_retries=config.max_retries,
            ) as client:
                result = IngestionPipeline(
                    client=client,
                    repository=repository,
                    base_url=config.base_url,
                    page_size=config.page_size,
                ).run(force=config.force)
        finally:
            repository.close()
    except Exception as error:
        print(f"Ingestão falhou: {error}", file=sys.stderr)
        return 1

    print(
        f"Ingestão {result.status}: ingestion_id={result.ingestion_id} "
        f"source_updated_at={result.source_updated_at.isoformat()}"
    )
    return 0


def _runtime_config(arguments: argparse.Namespace) -> RuntimeConfig:
    database_url = arguments.database_url
    if not isinstance(database_url, str) or not database_url.strip():
        raise ValueError("DATABASE_URL é obrigatória.")
    if not isinstance(arguments.base_url, str) or not arguments.base_url.strip():
        raise ValueError("OBRASGOV_BASE_URL é obrigatória.")
    if not 1 <= arguments.page_size <= MAX_PAGE_SIZE:
        raise ValueError(f"page-size deve estar entre 1 e {MAX_PAGE_SIZE}.")
    if arguments.timeout_seconds <= 0:
        raise ValueError("timeout-seconds deve ser maior que zero.")
    if arguments.max_retries < 0:
        raise ValueError("max-retries não pode ser negativo.")

    return RuntimeConfig(
        database_url=database_url,
        base_url=arguments.base_url,
        page_size=arguments.page_size,
        timeout_seconds=arguments.timeout_seconds,
        max_retries=arguments.max_retries,
        force=arguments.force,
    )


def _environment_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None else int(value)


def _environment_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return default if value is None else float(value)
