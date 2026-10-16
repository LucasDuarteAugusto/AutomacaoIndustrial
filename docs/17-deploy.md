# 17 — Deploy estável

Objetivo desta etapa: **subir a API de forma repetível** (imagem versionada + secrets + healthchecks), sem ainda precisar de Redis ou várias réplicas.

## O que já existe

| Peça | Onde |
|---|---|
| Imagem multi-stage | `backend/Dockerfile` |
| Compose local (db + api) | `docker-compose.yml` |
| Compose produção (override) | `docker-compose.prod.yml` |
| Secrets de exemplo | `.env.production.example` |
| CI (ruff, mypy, pytest, build) | `.github/workflows/ci.yml` |
| CD (push GHCR) | `.github/workflows/cd.yml` |

## Checklist antes de ir ao ar

1. **Postgres com pgvector** — Compose `db` ou banco gerenciado (Neon, RDS, Cloud SQL, etc.) com extensão `vector`.
2. **`JWT_SECRET` forte** (≥ 32 bytes aleatórios) — nunca o valor de desenvolvimento.
3. **`CORS_ORIGINS`** só com o(s) front(s) reais (`https://...`).
4. **Senha do Postgres** diferente do default `automacao`.
5. **Armazenamento** — volume persistente (`api_arquivos`) ou S3/R2.
6. **Chaves IA** — `VOYAGE_API_KEY` / `OPENAI_API_KEY` se for usar ingestão e agente.
7. Após o primeiro start: `POST /v1/auth/bootstrap` (só funciona com `USUARIOS` vazio).

Verificar: `GET /health` → 200; `GET /ready` → 200.

## Opção A — VPS / máquina com Docker

```powershell
# Na máquina de deploy (com Docker Compose v2.24+)
git clone <repo> && cd AutomacaoIndustrial
Copy-Item .env.production.example .env.production
# Edite POSTGRES_PASSWORD, JWT_SECRET, CORS_ORIGINS

docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d --build
```

- O Postgres **não** fica publicado na porta do host (override `ports: !reset []`).
- A API sobe em `${API_PORT:-8000}` e aplica migrations no start.
- Coloque um reverse proxy (Caddy/nginx/Traefik) na frente para TLS.

### Usar imagem do GHCR (sem build na VPS)

1. No GitHub: Actions → CD deve ter publicado `ghcr.io/<owner>/automacao-industrial-api:<branch>`.
2. No `.env.production`:

```env
API_IMAGE=ghcr.io/lucasduarteaugusto/automacao-industrial-api:development
```

3. Login no registry (pacote privado) e suba:

```powershell
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production pull api
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d
```

Pacotes GHCR: repositório → Packages; se estiver privado, a VPS precisa de um PAT com `read:packages`.

## Opção B — Banco gerenciado + só a API

1. Crie Postgres 16/17 com **pgvector** habilitado.
2. Rode a API (Compose só `api`, Kubernetes, Cloud Run, etc.) com:

```env
DATABASE_URL=postgresql+asyncpg://user:senha@host:5432/db
AMBIENTE=producao
LOG_JSON=true
JWT_SECRET=...
CORS_ORIGINS=https://...
RUN_MIGRATIONS=true
```

3. Prefira armazenamento `s3` (R2) para não depender de disco local efêmero.

## CD (GitHub Container Registry)

O workflow `CD` publica a imagem em push para `development` / `main` / `master` e em tags `v*`.

Tags típicas: `development`, `main`, `sha-<commit>`, `1.2.3` (semver).

Permissão necessária: **Settings → Actions → Workflow permissions → Read and write**.

## O que ainda não é esta entrega

- Rate limiting (próximo na ordem prática).
- Várias réplicas + load balancer.
- Redis (cache / filas).
- Terraform/Pulumi de um cloud específico.

## Próximo passo

**Rate limiting** na API (por IP e/ou por usuário JWT) para proteger login, busca e agente sob pico de uso.
