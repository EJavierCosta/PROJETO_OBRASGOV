FROM ghcr.io/astral-sh/uv:0.8.14-python3.12-bookworm-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./
ENV UV_HTTP_TIMEOUT=300
RUN uv sync --locked --no-dev --extra ingestion --no-install-project
COPY ingestion ./ingestion
RUN uv sync --locked --no-dev --extra ingestion

ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 app
RUN chown -R app:app /app
USER app

ENTRYPOINT ["python", "-m", "obrasgov_ingestion"]
