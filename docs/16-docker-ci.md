# 16 — Docker e CI

## Imagem da API

`backend/Dockerfile` (multi-stage com [uv](https://docs.astral.sh/uv/)):

1. **builder** — `uv sync --frozen --no-dev` a partir de `pyproject.toml` / `uv.lock`
2. **runtime** — Python 3.14 slim, usuário não-root, volume `/data/arquivos`

No start, `docker-entrypoint.sh` roda `alembic upgrade head` (desligue com `RUN_MIGRATIONS=false`) e sobe o Uvicorn.

```powershell
# Só a imagem
docker build -t automacao-industrial-api ./backend

# Stack completa (Postgres + API)
Copy-Item .env.example .env   # na raiz, se ainda não tiver
docker compose up -d --build --wait
```

API: <http://127.0.0.1:8000/docs> · health: <http://127.0.0.1:8000/health>

O `DATABASE_URL` do serviço `api` aponta para o host `db` (rede interna do Compose). A porta `5433` continua só para acesso do host (uv local / DBeaver).

## Desenvolvimento: dois modos

| Modo | Quando usar |
|---|---|
| `docker compose up -d db` + `uv run uvicorn` em `backend/` | Dia a dia com hot reload |
| `docker compose up -d --build` (db + api) | Validar a imagem / ambiente próximo de produção |

## CI (GitHub Actions)

Workflow [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) em push/PR para `development` / `main` / `master`:

| Job | O que faz |
|---|---|
| **quality** | `uv sync --group dev` → ruff format/check → mypy |
| **test** | `pytest` com testcontainers (`pgvector/pgvector:pg17`) — precisa Docker no runner |
| **docker** | Build da imagem (sem push) |

## Variáveis no Compose (raiz `.env`)

Além de `POSTGRES_*`, o serviço `api` lê `API_PORT`, `JWT_SECRET`, `CORS_ORIGINS`, `VOYAGE_API_KEY`, `OPENAI_API_KEY`, etc. Modelo: `.env.example` na raiz.

## CD

Publicação da imagem no GHCR: [17 — Deploy](17-deploy.md) (workflow `.github/workflows/cd.yml`).

## Próximo passo

Deploy estável na VPS/cloud; depois rate limiting.
