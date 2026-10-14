# 03 — Migrations (Alembic)

O Alembic é o controle de versão do schema. Cada arquivo em `backend/migrations/versions/` descreve uma mudança com `upgrade()` (aplica) e `downgrade()` (desfaz). O banco guarda na tabela `alembic_version` qual foi a última aplicada.

> Todos os comandos deste documento rodam a partir de `backend/`, e os caminhos abaixo são relativos a essa pasta.

## Arquivos envolvidos

| Arquivo (em `backend/`) | Papel |
|---|---|
| `pyproject.toml` → `[tool.alembic]` | Local das migrations, formato do nome do arquivo (data + hora + slug), hooks que rodam ruff no arquivo gerado |
| `alembic.ini` | Apenas configuração de logging |
| `migrations/env.py` | Lê `DATABASE_URL` do `Settings`, usa `Base.metadata` para o autogenerate e ignora tabelas que não são nossas (`include_object`) |
| `migrations/script.py.mako` | Modelo dos arquivos novos |
| `app/models.py` | Importa todos os models; o autogenerate só enxerga o que estiver importado aqui |

## Histórico atual

| Revisão | Arquivo | O que faz |
|---|---|---|
| `6a9c15cafac3` | `habilita_extensao_vector` | `CREATE EXTENSION vector` |
| `b1d21174385c` | `cria_catalogo_e_documentos` | Cria as 7 tabelas do catálogo e documentos |
| `add24d28b1b3` | `insere_tipos_equipamento_iniciais` | Insere os 3 tipos de equipamento iniciais |

## Comandos

```powershell
uv run alembic current                 # revisão aplicada no banco
uv run alembic history --verbose       # lista de revisões
uv run alembic upgrade head            # aplica tudo que falta
uv run alembic downgrade -1            # desfaz a última (somente banco local!)
uv run alembic check                   # falha se os models divergirem do banco
uv run alembic upgrade head --sql      # mostra o SQL sem executar
```

## Fluxo para alterar o schema

1. **Altere o model** em `app/<dominio>/models.py`, seguindo [as convenções](02-banco-de-dados.md#convenções). Model novo? Importe em `app/models.py`.
2. **Garanta o banco local na head**: `uv run alembic current`.
3. **Gere**: `uv run alembic revision --autogenerate -m "<verbo>_<objeto>"`. Nome em snake_case curto: `cria_trechos`, `adiciona_ativo_em_documentos`, `cria_idx_trechos_embedding`.
4. **Revise o arquivo à mão** (checklist abaixo). O autogenerate erra.
5. **Teste ida e volta** no banco local:

   ```powershell
   uv run alembic upgrade head
   uv run alembic downgrade -1
   uv run alembic upgrade head
   uv run alembic check
   uv run pytest
   ```

6. Commit da migration junto com o model.

## Checklist de revisão

- [ ] Contém só o que foi pedido (nenhum `drop_table` inesperado).
- [ ] Nomes físicos em MAIÚSCULO; PK/FK `Uuid` com `server_default=sa.text("gen_random_uuid()")`.
- [ ] `comment=` em toda coluna e tabela criada.
- [ ] Constraints e índices nomeados `PK_`/`UK_`/`FK_`/`IDX_`/`CK_`.
- [ ] Criação de tabela protegida por guard: `if not sa.inspect(op.get_bind()).has_table("X"):`.
- [ ] Coluna `NOT NULL` nova em tabela com dados: usar `server_default` ou fazer em 3 passos (nullable → preencher → `alter_column(nullable=False)`).
- [ ] Índice em tabela grande: `postgresql_concurrently=True` dentro de `with op.get_context().autocommit_block():`.
- [ ] `downgrade()` desfaz **só** o que o `upgrade()` fez, em ordem inversa. Nunca `pass`.
- [ ] Dados (seeds) em migration separada da estrutura.

## Armadilhas conhecidas

**Listas fixas (`Enum` com `native_enum=False`).** O autogenerate gera o `CHECK` duplicado (com o nome cru e com o nome da convenção) e ainda renderiza `sa.Enum(create_constraint=True)`, que criaria um terceiro. Na migration, use `sa.String(N)` na coluna e um único `sa.CheckConstraint(..., name="CK_<TABELA>_<COLUNA>")`. Veja `cria_catalogo_e_documentos` como referência.

**Alterar valores de uma lista fixa.** Adicionar um tipo de documento exige: atualizar o `StrEnum` no model e criar migration que remove e recria o `CHECK`:

```python
op.drop_constraint("CK_DOCUMENTOS_TIPO_DOCUMENTO", "DOCUMENTOS", type_="check")
op.create_check_constraint("CK_DOCUMENTOS_TIPO_DOCUMENTO", "DOCUMENTOS", '"TIPO_DOCUMENTO" IN (...)')
```

**`downgrade` em produção.** Desfazer pode apagar dados. Em produção, prefira uma nova migration "para frente" que corrija o problema. O hook do Cursor (`guarda-shell.py`) pede confirmação em qualquer `alembic downgrade`.

**Seeds e `downgrade`.** O `downgrade` de `insere_tipos_equipamento_iniciais` falha se alguma família usar esses tipos (FK `RESTRICT`). Isso é intencional.
