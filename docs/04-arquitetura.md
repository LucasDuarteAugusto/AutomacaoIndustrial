# 04 — Arquitetura

## Visão geral

```text
Clientes (React, Android, agente de IA)
        │ HTTP/JSON
        ▼
┌──────────────────────── FastAPI ────────────────────────┐
│ router  →  service  →  repository  →  model (SQLAlchemy)│
│ handlers de erro (problem+json) · logs (structlog)      │
│ Settings (.env) · engine + pool de conexões (asyncpg)   │
└────────────────────────────┬────────────────────────────┘
                             ▼
              PostgreSQL 17 + pgvector (Docker)
```

## Stack

| Peça | Versão | Por que |
|---|---|---|
| Python | 3.14 | Versão atual; tipagem moderna (`X \| None`, generics PEP 695) |
| uv | 0.12 | Gerencia Python e dependências; `uv.lock` garante instalação idêntica |
| FastAPI | 0.143 | Validação automática, OpenAPI gerado, assíncrono |
| Pydantic / pydantic-settings | 2.14 / 2.16 | Schemas de entrada/saída e configuração tipada |
| SQLAlchemy (async) | 2.1 | ORM maduro, suporte a pgvector, SQL explícito quando preciso |
| asyncpg | 0.32 | Driver PostgreSQL assíncrono mais rápido |
| Alembic | 1.20 | Versionamento do schema |
| structlog | 26.1 | Logs estruturados (console local, JSON em produção) |
| PostgreSQL + pgvector | 17 | Dados relacionais e vetores no mesmo banco |
| ruff / mypy | 0.17 / 2.4 | Lint+formatação / checagem de tipos strict |
| pytest + testcontainers | 9.1 / 4.15 | Testes contra Postgres real |

### Por que pgvector em vez de um banco vetorial separado

Os vetores ficam na mesma linha dos metadados. Uma única consulta filtra ("só SINAMICS G120, em português") e ordena por similaridade (`ORDER BY embedding <=> :pergunta`), sem sincronizar dois bancos. O PostgreSQL ainda oferece busca textual (`tsvector`) para combinar com a semântica, o que é essencial para códigos exatos como `F07801` ou `p1120`.

### Por que SQLAlchemy 2 (e não SQLModel, Tortoise ou SQL puro)

SQLModel é uma camada fina sobre o próprio SQLAlchemy e limita consultas complexas. Tortoise/Piccolo têm ecossistema menor. SQL puro com asyncpg obriga a escrever tudo à mão. O SQLAlchemy 2 tem tipagem com `Mapped[...]`, integração oficial com pgvector e Alembic, e permite SQL explícito quando necessário.

## Estrutura de pastas

```text
app/
  main.py               create_app(), lifespan, registro de routers e handlers
  models.py             importa todos os models (para o Alembic)
  core/
    config.py           Settings (lê .env)
    db.py               Base, NAMING_CONVENTION, TimestampMixin, engine, sessão
    deps.py             SessionDep
    errors.py           exceções de domínio (sem dependência de FastAPI)
    handlers.py         exceções → application/problem+json
    logging.py          configuração do structlog
    repository.py       RepositorioBase genérico (obter, paginar, adicionar, remover)
    schemas.py          Entrada, Saida, Pagina[T], PaginacaoDep, NaoNulo, DecimalJson
    servicos.py         aplicar_alteracoes, remover_ou_conflito
  health/router.py      /health e /ready
  catalogo/             tipos de equipamento, fabricantes, famílias, equipamentos
  documentos/           documentos e vínculos com famílias/equipamentos
migrations/             Alembic
tests/                  espelha app/
docs/                   esta documentação
```

Cada domínio segue o mesmo molde:

| Arquivo | Responsabilidade | Pode importar | Não pode |
|---|---|---|---|
| `router.py` | HTTP: recebe, valida (via schema), chama o service, devolve schema | `fastapi`, schemas, deps | Acessar `AsyncSession` direto |
| `deps.py` | Monta o service por requisição (`XServiceDep`) | `fastapi`, service | Regra de negócio |
| `schemas.py` | Pydantic: `XCreate`, `XUpdate`, `XOut` | `pydantic` | Models SQLAlchemy como saída |
| `service.py` | Regras de negócio, `commit`, exceções de domínio | repositories, schemas, `app.core.errors` | `fastapi`, `HTTPException` |
| `repository.py` | Consultas SQLAlchemy | models | Regra de negócio, `commit` |
| `models.py` | Mapeamento das tabelas | SQLAlchemy | — |

## Ciclo de vida de uma requisição

Exemplo: `POST /v1/familias`.

1. **Validação**: o FastAPI converte o JSON em `FamiliaCreate`. Campo faltando, extra, vazio ou UUID inválido → 422 antes de tocar no banco.
2. **Dependências**: `FamiliaServiceDep` pede `SessionDep`, que abre uma `AsyncSession` do pool só para esta requisição.
3. **Service**: confere se fabricante e tipo existem (senão `RegraNegocio` → 422) e se o nome está livre no fabricante (senão `Conflito` → 409). Cria o objeto via repository e faz `commit`.
4. **Resposta**: o service devolve `FamiliaOut`; o FastAPI serializa e responde 201.
5. **Fim**: a sessão é fechada e a conexão volta ao pool.

## Decisões transversais

**Fábrica `create_app(settings)`.** Permite criar a aplicação com outra configuração nos testes. Por isso o uvicorn usa `--factory`.

**`lifespan`.** Abre o engine na subida e fecha na descida (substitui `@app.on_event`).

**Erros RFC 9457.** Todo erro sai como `application/problem+json` com `type`, `title`, `status`, `detail`, `instance`. O frontend trata erros de um jeito só. Violação de integridade do banco que escapar das validações vira 409, nunca 500.

**Dupla proteção.** O service valida antes (mensagem clara) e o banco garante com `UNIQUE`/`FK`/`CHECK` (protege contra requisições simultâneas).

**Exclusão com vínculos.** O service tenta excluir; se a FK `RESTRICT` barrar, converte em 409 com orientação para desativar (`ativo=false`).

**`PATCH` parcial.** Só os campos enviados mudam (`model_dump(exclude_unset=True)`). Enviar `null` em campo obrigatório → 422 (`NaoNulo`).

**`eager_defaults`.** O `TimestampMixin` faz o SQLAlchemy buscar `createdAt`/`updatedAt` e o ID gerado via `RETURNING`, evitando consultas extras e erros de carregamento preguiçoso em código assíncrono.

**Relações N:N com `lazy="selectin"`.** `Documento.familias` e `Documento.equipamentos` são carregadas junto, em uma consulta extra por lote, evitando carregamento implícito (proibido em async).

## Configuração para IA (`.cursor/`)

| Pasta | Conteúdo |
|---|---|
| `rules/` | Convenções que o assistente segue: versões da stack, arquitetura, banco, testes, branches protegidas |
| `hooks/` | Bloqueio de `pip install` e push em branch protegida, proteção de arquivos `.env`, formatação automática, verificação ao final de cada tarefa |
| `skills/` | Roteiros para criar endpoint completo (`novo-endpoint`) e migration (`migration-alembic`) |
