FROM ghcr.io/astral-sh/uv:0.8.14-python3.12-bookworm-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./
ENV UV_HTTP_TIMEOUT=300
RUN uv sync --locked --no-dev --extra transform --no-install-project
COPY dbt ./dbt

ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 app
RUN chown -R app:app /app
USER app

ENTRYPOINT ["dbt"]
