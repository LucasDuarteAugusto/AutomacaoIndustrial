# 06 — Testes

## Rodando

Comandos e caminhos deste documento são relativos a `backend/`.

```powershell
uv run pytest                          # todos (Docker Desktop precisa estar aberto)
uv run pytest tests/catalogo -q        # um domínio
uv run pytest -k fabricante            # por nome
uv run pytest -x --lf                  # para no primeiro erro; roda só os que falharam antes
```

A primeira execução baixa a imagem `pgvector/pgvector:pg17` (uma vez).

## Como funciona

```text
pytest inicia
  └─ database_url (sessão): sobe container Postgres+pgvector e aplica as migrations reais
       └─ app (sessão): create_app(settings de teste) + lifespan (abre o engine)
            └─ db_session (por teste): abre transação
                 └─ client (por teste): httpx.AsyncClient chamando a app em memória,
                                        com get_session e get_usuario_atual substituídos
            fim do teste: rollback (nada persiste)
```

Pontos importantes:

- **Banco real, não simulado.** Mesma imagem do `docker-compose.yml`. Constraints, `CHECK`, FKs e pgvector se comportam como em produção. SQLite e mock de `AsyncSession` são proibidos no projeto.
- **Migrations testadas a cada execução.** O banco de teste é criado pelo `alembic upgrade head`; uma migration quebrada derruba a suíte.
- **Isolamento por transação.** Cada teste roda dentro de uma transação desfeita no final. O `commit` do service vira um savepoint (`join_transaction_mode="create_savepoint"`). Nenhum teste precisa limpar tabelas.
- **Auth nos testes.** O `client` padrão sobrescreve `get_usuario_atual` com um ADMIN sintético. Use `client_sem_auth` (Bearer real) ou `client_leitura` quando o teste for de autenticação/perfil.
- **Sem rede.** O `AsyncClient` usa `ASGITransport` e chama a aplicação diretamente.
- **Assíncrono automático.** `asyncio_mode = "auto"` no `pyproject.toml`: não precisa de `@pytest.mark.asyncio`.

## Estrutura

```text
tests/
  conftest.py                  fixtures: database_url, settings, app, db_session, client, client_sem_auth, client_leitura
  factories.py                 factories (polyfactory) + helpers criar_fabricante/familia/equipamento/documento
  core/                        handlers de erro, migrations/pgvector
  health/                      /health e /ready
  auth/                        login, bootstrap, JWT, CORS, perfil LEITURA
  agente/                      Q&A com LLM fake e citações
  catalogo/                    tipos, fabricantes, famílias, equipamentos
  documentos/                  documentos e vínculos
```

## Escrevendo um teste novo

Padrão Arrange / Act / Assert, nome descrevendo o comportamento:

```python
async def test_criar_equipamento_com_codigo_repetido_na_familia_retorna_409(client: AsyncClient) -> None:
    equipamento = await criar_equipamento(client, codigo_pedido="3RW5524-1HA14")

    resp = await client.post(
        "/v1/equipamentos",
        json={"id_familia": equipamento["id_familia"], "codigo_pedido": "3rw5524-1ha14", "nome": "Outro"},
    )

    assert resp.status_code == 409
```

Os helpers de `tests/factories.py` criam as dependências automaticamente: `criar_equipamento(client)` cria fabricante e família se você não passar `id_familia`. Passe só o que importa para o teste.

## O que todo endpoint novo deve cobrir

- Caminho feliz (status e corpo).
- 404 para ID inexistente.
- 409 para duplicidade e vínculos, quando aplicável.
- 422 para entrada inválida e referência inexistente.
- Filtros e paginação das listagens.

## Regras

- Mock só em fronteira externa (APIs de terceiros com `respx`, relógio, fila). Nunca mockar service ou repository em teste de rota.
- Dados via factories, não dicionários enormes inline.
- `tests/` espelha `app/`.

## Qualidade antes de commit

```powershell
uv run ruff format .
uv run ruff check --fix .
uv run mypy
uv run pytest
```
