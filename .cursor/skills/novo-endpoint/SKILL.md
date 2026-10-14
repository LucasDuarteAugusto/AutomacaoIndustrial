---
name: novo-endpoint
description: >-
  Cria um domínio/endpoint FastAPI completo (model, schemas, repository,
  service, router, testes e migration) seguindo as rules do repo. Use quando o
  usuário pedir /novo-endpoint, novo endpoint, novo CRUD, nova rota ou novo
  domínio na API Python.
disable-model-invocation: true
---

# Novo endpoint

Monorepo: caminhos (`app/`, `tests/`, `migrations/`) e comandos `uv run ...` são relativos a `backend/`.

## Requisito mínimo

Exija antes de gerar código:

- **Domínio** (ex.: `clientes`) e **entidade** (ex.: `Cliente`).
- **Tabela física** (ex.: `CLIENTESCONTATOS`) e se ela **já existe** (de outro sistema) ou é **nova** deste serviço.
- **Operações** (listar, obter, criar, alterar, excluir) e campos com tipo/obrigatoriedade.

Se faltar algo, pergunte. Não invente nome de tabela nem coluna.

## Checklist

```
- [ ] 1. Branch não protegida (rule protected-branches)
- [ ] 2. Ler rules: stack-versions, fastapi-arquitetura, estrutura-banco, testes-python
- [ ] 3. Tabela existente? Ler a migration Sequelize em tdpcloud-backend-node/src/migrations
- [ ] 4. models.py
- [ ] 5. schemas.py
- [ ] 6. repository.py
- [ ] 7. service.py
- [ ] 8. router.py + registrar em app/main.py
- [ ] 9. Migration (só se tabela nova) → skill migration-alembic
- [ ] 10. Testes
- [ ] 11. Validar
```

## Passos

**3. Tabela existente.** Copie nomes físicos e tipos exatamente da migration Sequelize. Use `graphify query` se existir `graphify-out/graph.json`.

**4. models.py.** Mapeamento conforme `estrutura-banco.mdc`: atributo snake_case, nome físico MAIÚSCULO explícito, UUID com `gen_random_uuid()`, `comment` em cada campo. Coluna de tenant obrigatória quando a tabela é de tenant.

**5. schemas.py.** Três classes:

```python
class ClienteBase(BaseModel):
    nome: str = Field(min_length=1, max_length=200)


class ClienteCreate(ClienteBase): ...


class ClienteUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=200)


class ClienteOut(ClienteBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
```

**6. repository.py.** Classe recebe `AsyncSession`. Métodos `obter`, `listar(limit, offset) -> tuple[list[T], int]`, `adicionar`, `remover`. Sempre filtra por tenant. Sem `commit`.

**7. service.py.** Recebe o repository. Regra de negócio, `commit`, e exceções de `app/core/errors.py`. Não importa `fastapi`.

**8. router.py.** `APIRouter(prefix="/v1/<dominio>", tags=["<dominio>"])`. Status codes: 201 criar, 204 excluir. Dependency alias `<Entidade>ServiceDep` em `deps.py` do domínio. Registrar com `app.include_router(...)`.

**10. Testes.** Em `tests/<dominio>/`: `test_router.py` cobrindo, por operação, caminho feliz + 404/409/422 relevantes + isolamento de tenant. Factory em `tests/factories.py`.

**11. Validar** (repita até passar):

```bash
uv run ruff format . && uv run ruff check --fix .
uv run mypy app
uv run pytest tests/<dominio> -x -q
```

## Saída

Resumo curto: arquivos criados, rotas (`MÉTODO /v1/...` → status), migration gerada (ou "tabela existente, sem migration"), resultado dos testes.
