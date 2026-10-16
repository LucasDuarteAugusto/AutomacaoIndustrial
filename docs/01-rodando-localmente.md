# 01 — Rodando localmente

## Pré-requisitos

| Ferramenta | Versão testada | Para quê |
|---|---|---|
| [uv](https://docs.astral.sh/uv/) | 0.12+ | Gerencia Python, dependências e executa comandos |
| Python | 3.14 | Instalado automaticamente pelo `uv` se faltar (fixado em `backend/.python-version`) |
| Docker Desktop | 29+ com Compose v2 | Banco PostgreSQL + pgvector e testes com testcontainers |
| Git | 2.4x+ | Controle de versão |

Não use `pip install` nem ative a venv manualmente: tudo roda via `uv run`.

## Organização do repositório (monorepo)

```text
AutomacaoIndustrial/
├── docker-compose.yml   Postgres + API (opcional)                 → comandos docker na RAIZ
├── docker-compose.prod.yml  override de deploy estável
├── .env                 variáveis do docker-compose
├── .github/workflows/   CI + CD (GHCR)
├── docs/
└── backend/             projeto Python (FastAPI)                   → comandos uv na pasta backend/
    ├── Dockerfile       imagem da API
    ├── .env             variáveis da aplicação (DATABASE_URL…)
    ├── pyproject.toml, uv.lock, alembic.ini
    ├── app/  migrations/  tests/
```

Regra prática: **`docker compose` na raiz, `uv run` dentro de `backend/`.** Detalhes da imagem e do CI: [16 — Docker e CI](16-docker-ci.md).

## Primeira execução

```powershell
git clone https://github.com/LucasDuarteAugusto/AutomacaoIndustrial.git
cd AutomacaoIndustrial

# 1. Configuração do banco (raiz) — só o Postgres
#    (não use "docker compose up" sem "db": isso também sobe a API na 8000
#     e conflita com o uvicorn local abaixo)
Copy-Item .env.example .env
docker compose up -d db --wait

# 2. Backend: configuração, dependências e tabelas
cd backend
Copy-Item .env.example .env
# Opcional para ingestão/agente: edite .env e preencha VOYAGE_API_KEY / OPENAI_API_KEY
uv sync
uv run alembic upgrade head

# 3. Sobe a API com recarga automática ao salvar arquivos
uv run uvicorn app.main:create_app --factory --reload
```

Depois disso:

| Endereço | O que é |
|---|---|
| <http://127.0.0.1:8000/docs> | Swagger UI: testar rotas pelo navegador |
| <http://127.0.0.1:8000/redoc> | Documentação em formato de leitura |
| <http://127.0.0.1:8000/health> | Processo vivo |
| <http://127.0.0.1:8000/ready> | Banco acessível |

Roteiro de validação (bootstrap → catálogo → PDF → busca → agente): [00 — Guia de teste manual](00-guia-teste-manual.md).

**Swagger + JWT:** em `/docs`, use **Authorize**, cole o `access_token` do bootstrap/login (com ou sem o prefixo `Bearer `, conforme a UI) e as demais rotas `/v1` passam a enviar o header.

## Configuração

Os arquivos `.env` não vão para o git; os `.env.example` são os modelos.

### `.env` da raiz — usado pelo `docker-compose.yml`

| Variável | Padrão | Descrição |
|---|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `automacao` / `automacao` / `automacao_industrial` | Criados no primeiro start do container |
| `POSTGRES_PORT` | `5433` | Porta no seu computador que aponta para o 5432 do container |

### `backend/.env` — lido por `backend/app/core/config.py` (`Settings`)

O modelo completo está em `backend/.env.example` (copie para `.env` e preencha as chaves vazias quando for usar cada serviço).

| Variável | Preencher agora? | Padrão / exemplo | Descrição |
|---|---|---|---|
| `AMBIENTE` | Sim | `local` | `local`, `teste` ou `producao` |
| `LOG_LEVEL` | Sim | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_JSON` | Sim | `false` | `true` emite logs em JSON (produção) |
| `DATABASE_URL` | Sim | `postgresql+asyncpg://automacao:automacao@localhost:5433/automacao_industrial` | API e Alembic; deve bater com o `.env` da raiz |
| `ARMAZENAMENTO_TIPO` | Sim | `local` | `local` (disco) ou `s3` (R2 / AWS) |
| `ARMAZENAMENTO_CAMINHO` | Sim (se local) | `data/arquivos` | Pasta dos PDFs; ver [10 — Armazenamento](10-armazenamento.md) |
| `ARMAZENAMENTO_TAMANHO_MAX_BYTES` | Opcional | `52428800` | Limite do upload de PDF (50 MiB) |
| `INGESTAO_TAMANHO_TRECHO_CHARS` | Opcional | `2500` | Tamanho alvo dos trechos na ingestão |
| `INGESTAO_MAX_CHARS_LOTE_EMBEDDING` | Opcional | `80000` | Limite por lote no Voyage contextualizado |
| `BUSCA_CANDIDATOS_POR_MODO` | Opcional | `40` | Candidatos por modo na busca híbrida |
| `BUSCA_RRF_K` | Opcional | `60` | Constante do Reciprocal Rank Fusion |
| `S3_ENDPOINT_URL` | Só se `s3` (R2) | *(vazio)* | Endpoint R2; omitir na AWS |
| `S3_REGION` | Só se `s3` | `auto` | `auto` no R2; região AWS depois |
| `S3_BUCKET` | Só se `s3` | *(vazio)* | Nome do bucket |
| `S3_ACCESS_KEY_ID` | Só se `s3` | *(vazio)* | Access key |
| `S3_SECRET_ACCESS_KEY` | Só se `s3` | *(vazio)* | Secret key |
| `VOYAGE_API_KEY` | Na ingestão | *(vazio)* | Embedding `voyage-context-4` |
| `VOYAGE_BASE_URL` | Opcional | `https://api.voyageai.com/v1` | |
| `EMBEDDING_MODELO` | Opcional | `voyage-context-4` | |
| `EMBEDDING_DIMENSAO` | Opcional | `1024` | Deve bater com `TRECHOS.EMBEDDING` |
| `OPENAI_API_KEY` | No agente | *(vazio)* | LLM `gpt-5-mini` |
| `OPENAI_BASE_URL` | Opcional | `https://api.openai.com/v1` | |
| `LLM_MODELO` | Opcional | `gpt-5-mini` | |
| `JWT_SECRET` | Sim (trocar fora do PC local) | valor de exemplo | Assinatura do token — ver [13](13-auth.md) |
| `JWT_EXPIRACAO_MINUTOS` | Opcional | `480` | Validade do access token |
| `CORS_ORIGINS` | Se for usar frontend | `http://localhost:5173,...` | Origens permitidas |
| `RATE_LIMIT_HABILITADO` | Opcional | `true` | Ver [18](18-rate-limit.md) |
| `RATE_LIMIT_BACKEND` | Opcional | `memoria` | `memoria` ou `redis` |
| `REDIS_URL` | Se backend=redis | — | Ex.: `redis://localhost:6379/0` |

Opcionais de pool (padrão no código): `DB_POOL_SIZE` (5), `DB_MAX_OVERFLOW` (10), `DB_ECHO` (`false`). Lista completa comentada: `backend/.env.example`.

## Comandos do dia a dia

Na **raiz**:

```powershell
docker compose up -d --wait          # sobe só o que já estava (ex.: db)
docker compose up -d db --wait       # só o Postgres (dev com uvicorn local)
docker compose up -d --build --wait  # Postgres + API (imagem)
docker compose stop                  # para (mantém os dados)
docker compose down                  # remove containers (mantém volumes)
docker compose down -v               # remove containers E volumes (zera o banco)
docker compose logs -f db            # logs do Postgres
docker compose logs -f api           # logs da API

# psql dentro do container
docker exec -it automacao-industrial-db psql -U automacao -d automacao_industrial
```

Em **`backend/`**:

```powershell
uv run uvicorn app.main:create_app --factory --reload   # API

uv run ruff format .                 # formata
uv run ruff check --fix .            # lint
uv run mypy                          # tipos (modo strict)
uv run pytest                        # testes (precisa do Docker rodando)

uv add <pacote>                      # dependência de produção
uv add --dev <pacote>                # dependência de desenvolvimento
```

Para conectar uma ferramenta gráfica (DBeaver, pgAdmin, DataGrip): host `localhost`, porta `5433`, usuário `automacao`, senha `automacao`, banco `automacao_industrial`.

## Hooks de pre-commit (recomendado)

O `.pre-commit-config.yaml` (raiz) roda ruff nos arquivos de `backend/`, verifica o `backend/uv.lock`, procura senhas com gitleaks, bloqueia commit em `development`/`master`/`main` e roda mypy no push. Para ativar uma vez, na raiz:

```powershell
uv tool install pre-commit
pre-commit install
```

## Solução de problemas

| Sintoma | Causa provável | Solução |
|---|---|---|
| `password authentication failed for user "automacao"` | Outro PostgreSQL (instalado no Windows) está na mesma porta e recebe a conexão | Troque `POSTGRES_PORT` no `.env` da raiz e a porta da `DATABASE_URL` em `backend/.env`. Verifique com `Get-NetTCPConnection -LocalPort 5433 -State Listen` |
| `ValidationError ... database_url Field required` | Falta o `backend/.env` ou você rodou fora de `backend/` | `cd backend; Copy-Item .env.example .env` |
| `No config file 'alembic.ini' found` ou `No such file pyproject.toml` | Comando `uv run` executado na raiz | Rode a partir de `backend/` |
| `no configuration file provided` no `docker compose` | Comando docker executado dentro de `backend/` | Rode na raiz |
| `/ready` retorna 503 | Container parado ou porta errada | `docker compose ps`; `docker compose up -d --wait` |
| Testes falham com erro de Docker | Docker Desktop não está aberto | Abra o Docker Desktop e rode de novo |
| Tabela não existe ao chamar a API | Migrations não aplicadas | Em `backend/`: `uv run alembic upgrade head` |
| Porta 8000 já em uso / uvicorn não sobe | Serviço `api` do Compose também está rodando | `docker compose stop api` e use só `db`; ou teste só pela imagem (`docker compose up -d --build`) |
| 401 em todas as rotas `/v1` | Sem Bearer no Swagger | Bootstrap/login + **Authorize** em `/docs` — [00](00-guia-teste-manual.md) |
| Upload OK mas documento não fica `INDEXADO` | Sem `VOYAGE_API_KEY` ou PDF sem texto | Preencha a chave; veja `erro_processamento` no GET do documento |
| Agente retorna 503 | Sem `OPENAI_API_KEY` | Preencha no `backend/.env` e reinicie o uvicorn |
| 429 Limite de requisições | Rate limit | Aguarde ~1 min ou aumente `RATE_LIMIT_*` / desligue com `RATE_LIMIT_HABILITADO=false` |
