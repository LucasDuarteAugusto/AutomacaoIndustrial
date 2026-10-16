# syntax=docker/dockerfile:1
# Build: docker build -t automacao-industrial-api ./backend

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./


FROM python:3.14-slim-bookworm AS runtime

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data/arquivos \
    && chown -R appuser:appuser /data

COPY --from=builder --chown=appuser:appuser /app /app
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN sed -i 's/\r$//' /app/docker-entrypoint.sh \
    && chmod +x /app/docker-entrypoint.sh \
    && chown appuser:appuser /app/docker-entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    AMBIENTE=producao \
    LOG_JSON=true \
    ARMAZENAMENTO_TIPO=local \
    ARMAZENAMENTO_CAMINHO=/data/arquivos \
    RUN_MIGRATIONS=true

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
