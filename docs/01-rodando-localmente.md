# 01 — Rodando localmente

## Pré-requisitos

| Ferramenta | Versão testada | Para quê |
|---|---|---|
| [uv](https://docs.astral.sh/uv/) | 0.12+ | Gerencia Python, dependências e executa comandos |
| Python | 3.14 | Instalado automaticamente pelo `uv` se faltar (fixado em `.python-version`) |
| Docker Desktop | 29+ com Compose v2 | Banco PostgreSQL + pgvector e testes com testcontainers |
| Git | 2.4x+ | Controle de versão |

Não use `pip install` nem ative a venv manualmente: tudo roda via `uv run`.

## Primeira execução

```powershell
git clone https://github.com/LucasDuarteAugusto/AutomacaoIndustrial.git
cd AutomacaoIndustrial

# 1. Instala Python 3.14 (se preciso) e todas as dependências travadas no uv.lock
uv sync

# 2. Cria o arquivo de configuração local a partir do modelo
Copy-Item .env.example .env

# 3. Sobe o PostgreSQL 17 com pgvector e espera ficar saudável
docker compose up -d --wait

# 4. Cria/atualiza as tabelas
uv run alembic upgrade head

# 5. Sobe a API com recarga automática ao salvar arquivos
uv run uvicorn app.main:create_app --factory --reload
```

Depois disso:

| Endereço | O que é |
|---|---|
| <http://127.0.0.1:8000/docs> | Swagger UI: testar rotas pelo navegador |
| <http://127.0.0.1:8000/redoc> | Documentação em formato de leitura |
| <http://127.0.0.1:8000/health> | Processo vivo |
| <http://127.0.0.1:8000/ready> | Banco acessível |

## Configuração (`.env`)

Lido por `app/core/config.py` (`Settings`). O `.env` não vai para o git; o `.env.example` é o modelo.

| Variável | Padrão no exemplo | Descrição |
|---|---|---|
| `AMBIENTE` | `local` | `local`, `teste` ou `producao` |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_JSON` | `false` | `true` emite logs em JSON (produção) |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `automacao` / `automacao` / `automacao_industrial` | Usados pelo `docker-compose.yml` para criar o banco |
| `POSTGRES_PORT` | `5433` | Porta no seu computador que aponta para o 5432 do container |
| `DATABASE_URL` | `postgresql+asyncpg://automacao:automacao@localhost:5433/automacao_industrial` | URL usada pela API e pelo Alembic |

Opcionais (têm padrão no código): `DB_POOL_SIZE` (5), `DB_MAX_OVERFLOW` (10), `DB_ECHO` (`false`, `true` imprime todo SQL executado).

## Comandos do dia a dia

```powershell
# Banco
docker compose up -d --wait          # sobe
docker compose stop                  # para (mantém os dados)
docker compose down                  # remove o container (mantém os dados no volume)
docker compose down -v               # remove container E dados (zera o banco)
docker compose logs -f db            # acompanha logs do Postgres

# Acessar o banco pelo terminal (psql dentro do container)
docker exec -it automacao-industrial-db psql -U automacao -d automacao_industrial

# API
uv run uvicorn app.main:create_app --factory --reload

# Qualidade
uv run ruff format .                 # formata
uv run ruff check --fix .            # lint
uv run mypy                          # tipos (modo strict)
uv run pytest                        # testes (precisa do Docker rodando)

# Dependências
uv add <pacote>                      # dependência de produção
uv add --dev <pacote>                # dependência de desenvolvimento
```

Para conectar uma ferramenta gráfica (DBeaver, pgAdmin, DataGrip): host `localhost`, porta `5433`, usuário `automacao`, senha `automacao`, banco `automacao_industrial`.

## Hooks de pre-commit (recomendado)

O repositório tem `.pre-commit-config.yaml` com ruff, verificação do `uv.lock`, gitleaks (detecção de senhas), bloqueio de commit em `development`/`master`/`main` e mypy no push. Para ativar uma vez:

```powershell
uv tool install pre-commit
pre-commit install
```

## Solução de problemas

| Sintoma | Causa provável | Solução |
|---|---|---|
| `password authentication failed for user "automacao"` | Outro PostgreSQL (instalado no Windows) está na mesma porta e recebe a conexão | Use outra porta: ajuste `POSTGRES_PORT` e a porta em `DATABASE_URL`. Verifique com `Get-NetTCPConnection -LocalPort 5433 -State Listen` |
| `ValidationError ... database_url Field required` | Falta o `.env` ou a variável `DATABASE_URL` | `Copy-Item .env.example .env` |
| `/ready` retorna 503 | Container parado ou porta errada | `docker compose ps`; `docker compose up -d --wait` |
| Testes falham com erro de Docker | Docker Desktop não está aberto | Abra o Docker Desktop e rode de novo |
| `No config file 'alembic.ini' found` | Comando executado fora da raiz do projeto | Rode a partir da pasta que contém `pyproject.toml` |
| Tabela não existe ao chamar a API | Migrations não aplicadas | `uv run alembic upgrade head` |
