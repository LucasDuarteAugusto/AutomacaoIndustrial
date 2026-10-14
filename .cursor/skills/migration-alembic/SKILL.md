---
name: migration-alembic
description: >-
  Gera, revisa e valida migrations Alembic seguindo as convenções do banco
  INPERA (MAIÚSCULO, UUID, comment, downgrade reversível). Use quando o usuário
  pedir /migration-alembic, migration, alembic, criar/alterar tabela ou
  coluna na API Python.
disable-model-invocation: true
---

# Migration Alembic

Monorepo: rode os comandos `uv run alembic ...` a partir de `backend/`.

## Requisito mínimo

Exija a **mudança** (criar tabela, adicionar coluna, índice, etc.) e confirme que a tabela é **deste serviço**. Tabela que pertence ao `tdpcloud-backend-node` (Sequelize) não recebe migration aqui: avise e pare.

## Checklist

```
- [ ] 1. Branch não protegida
- [ ] 2. Banco local de pé e na head: uv run alembic current
- [ ] 3. Model alterado conforme estrutura-banco.mdc
- [ ] 4. Gerar: uv run alembic revision --autogenerate -m "<verbo>_<objeto>"
- [ ] 5. Revisar o arquivo gerado (checklist abaixo)
- [ ] 6. Testar ida e volta
- [ ] 7. Registrar no resumo
```

## Nome

Mensagem em snake_case curto: `cria_post_modelos`, `adiciona_ativo_em_post_modelos`, `cria_idx_post_modelos_nome`.

## Revisão do arquivo gerado

O autogenerate erra. Corrija à mão:

- [ ] Só contém o que foi pedido (sem drop de tabela de outro sistema — se aparecer, ajuste `include_object` no `env.py`, não apague só no arquivo).
- [ ] Nomes físicos MAIÚSCULOS; PK/FK `UUID` com `server_default=sa.text("gen_random_uuid()")`; nenhuma PK/FK `Integer`/`BigInteger`.
- [ ] `comment=` em toda coluna criada.
- [ ] Constraints/índices nomeados `IDX_`/`UK_`/`FK_`/`CK_`.
- [ ] Criação de tabela com guard:
  ```python
  if not sa.inspect(op.get_bind()).has_table("POST_MODELOS"):
      op.create_table(...)
  ```
- [ ] Coluna `NOT NULL` em tabela com dados: adicionar com `server_default` ou em 3 passos (nullable → backfill → `alter_column(nullable=False)`).
- [ ] Índice em tabela grande: `postgresql_concurrently=True` dentro de `with op.get_context().autocommit_block():`.
- [ ] `downgrade()` desfaz **só** o que o `upgrade()` criou, na ordem inversa. Nunca `pass`.
- [ ] Sem `op.execute` com SQL concatenado; dado de catálogo em migration separada.

## Testar ida e volta

Somente contra banco **local** (`DATABASE_URL` em `localhost`/container). Se a URL apontar para outro host, pare e avise.

```bash
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
uv run alembic check   # sem diferença entre models e banco
uv run pytest -x -q
```

O hook `guarda-shell.py` pede confirmação em `alembic downgrade`; isso é esperado.

## Saída

Arquivo da migration, resumo do que cria/altera, e resultado de `upgrade → downgrade → upgrade` e `alembic check`.
