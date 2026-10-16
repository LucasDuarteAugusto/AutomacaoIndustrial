"""cria_parametros_e_falhas

Create Date: 2026-10-16 11:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "d8f3a1b2c4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID_PADRAO = sa.text("gen_random_uuid()")
IDIOMAS = ("pt-BR", "en")
TIPOS_FALHA = ("FALHA", "ALARME")


def _nao_existe(tabela: str) -> bool:
    return not sa.inspect(op.get_bind()).has_table(tabela)


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "createdAt",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="Data de criação do registro",
        ),
        sa.Column(
            "updatedAt",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="Data da última alteração do registro",
        ),
    ]


def upgrade() -> None:
    if _nao_existe("PARAMETROS"):
        op.create_table(
            "PARAMETROS",
            sa.Column(
                "ID_PARAMETRO",
                sa.Uuid(),
                server_default=UUID_PADRAO,
                nullable=False,
                comment="Identificador do parâmetro",
            ),
            sa.Column("ID_FAMILIA", sa.Uuid(), nullable=False, comment="Família à qual o parâmetro pertence"),
            sa.Column(
                "VERSAO_FIRMWARE",
                sa.String(30),
                nullable=True,
                comment="Firmware alvo; nulo = vale para qualquer versão",
            ),
            sa.Column("CODIGO", sa.String(40), nullable=False, comment="Código do parâmetro (ex.: p1120, P0100)"),
            sa.Column("NOME", sa.String(200), nullable=True, comment="Nome curto / rótulo de menu"),
            sa.Column("DESCRICAO", sa.Text(), nullable=False, comment="Descrição técnica do parâmetro"),
            sa.Column("UNIDADE", sa.String(30), nullable=True, comment="Unidade (s, Hz, A, %, …)"),
            sa.Column(
                "VALOR_MIN",
                sa.Numeric(18, 6),
                nullable=True,
                comment="Limite inferior numérico, se aplicável",
            ),
            sa.Column(
                "VALOR_MAX",
                sa.Numeric(18, 6),
                nullable=True,
                comment="Limite superior numérico, se aplicável",
            ),
            sa.Column(
                "VALOR_PADRAO",
                sa.String(100),
                nullable=True,
                comment="Valor de fábrica (texto; pode ser enum)",
            ),
            sa.Column("GRUPO", sa.String(80), nullable=True, comment="Grupo/menu no equipamento"),
            sa.Column(
                "SOMENTE_LEITURA",
                sa.Boolean(),
                server_default=sa.false(),
                nullable=False,
                comment="Parâmetro não editável no equipamento",
            ),
            sa.Column("IDIOMA", sa.String(5), nullable=False, comment="Idioma do texto (pt-BR, en)"),
            sa.Column(
                "ID_DOCUMENTO",
                sa.Uuid(),
                nullable=True,
                comment="Documento de origem (lista de parâmetros), se houver",
            ),
            sa.Column("PAGINA", sa.Integer(), nullable=True, comment="Página de origem no documento"),
            sa.Column(
                "ATIVO",
                sa.Boolean(),
                server_default=sa.true(),
                nullable=False,
                comment="Registro disponível para consulta",
            ),
            *_timestamps(),
            sa.PrimaryKeyConstraint("ID_PARAMETRO", name="PK_PARAMETROS"),
            sa.ForeignKeyConstraint(
                ["ID_FAMILIA"],
                ["FAMILIAS.ID_FAMILIA"],
                name="FK_PARAMETROS_ID_FAMILIA_FAMILIAS",
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["ID_DOCUMENTO"],
                ["DOCUMENTOS.ID_DOCUMENTO"],
                name="FK_PARAMETROS_ID_DOCUMENTO_DOCUMENTOS",
                ondelete="SET NULL",
            ),
            sa.CheckConstraint(
                '"IDIOMA" IN (' + ", ".join(f"'{i}'" for i in IDIOMAS) + ")",
                name="CK_PARAMETROS_IDIOMA_PARAMETRO",
            ),
            comment="Parâmetros estruturados de comissionamento por família e firmware",
        )
        op.create_index("IX_PARAMETROS_ID_FAMILIA", "PARAMETROS", ["ID_FAMILIA"])
        op.create_index("IX_PARAMETROS_CODIGO", "PARAMETROS", ["CODIGO"])
        op.execute(
            """
            CREATE UNIQUE INDEX "UK_PARAMETROS_ESCOPO"
            ON "PARAMETROS" (
                "ID_FAMILIA",
                lower("CODIGO"),
                "IDIOMA",
                COALESCE("VERSAO_FIRMWARE", '')
            )
            """
        )

    if _nao_existe("FALHAS"):
        op.create_table(
            "FALHAS",
            sa.Column(
                "ID_FALHA",
                sa.Uuid(),
                server_default=UUID_PADRAO,
                nullable=False,
                comment="Identificador da falha/alarme",
            ),
            sa.Column("ID_FAMILIA", sa.Uuid(), nullable=False, comment="Família à qual o código pertence"),
            sa.Column(
                "VERSAO_FIRMWARE",
                sa.String(30),
                nullable=True,
                comment="Firmware alvo; nulo = vale para qualquer versão",
            ),
            sa.Column("CODIGO", sa.String(40), nullable=False, comment="Código (ex.: F07801, A0503)"),
            sa.Column("TIPO", sa.String(20), nullable=False, comment="FALHA ou ALARME"),
            sa.Column("TITULO", sa.String(200), nullable=False, comment="Nome curto do evento"),
            sa.Column("DESCRICAO", sa.Text(), nullable=True, comment="Descrição detalhada"),
            sa.Column("CAUSA", sa.Text(), nullable=True, comment="Causa provável"),
            sa.Column("SOLUCAO", sa.Text(), nullable=True, comment="Ação corretiva recomendada"),
            sa.Column("REACAO", sa.String(50), nullable=True, comment="Reação do equipamento (parada, aviso, …)"),
            sa.Column("IDIOMA", sa.String(5), nullable=False, comment="Idioma do texto (pt-BR, en)"),
            sa.Column("ID_DOCUMENTO", sa.Uuid(), nullable=True, comment="Documento de origem, se houver"),
            sa.Column("PAGINA", sa.Integer(), nullable=True, comment="Página de origem no documento"),
            sa.Column(
                "ATIVO",
                sa.Boolean(),
                server_default=sa.true(),
                nullable=False,
                comment="Registro disponível para consulta",
            ),
            *_timestamps(),
            sa.PrimaryKeyConstraint("ID_FALHA", name="PK_FALHAS"),
            sa.ForeignKeyConstraint(
                ["ID_FAMILIA"],
                ["FAMILIAS.ID_FAMILIA"],
                name="FK_FALHAS_ID_FAMILIA_FAMILIAS",
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["ID_DOCUMENTO"],
                ["DOCUMENTOS.ID_DOCUMENTO"],
                name="FK_FALHAS_ID_DOCUMENTO_DOCUMENTOS",
                ondelete="SET NULL",
            ),
            sa.CheckConstraint(
                '"TIPO" IN (' + ", ".join(f"'{t}'" for t in TIPOS_FALHA) + ")",
                name="CK_FALHAS_TIPO_FALHA",
            ),
            sa.CheckConstraint(
                '"IDIOMA" IN (' + ", ".join(f"'{i}'" for i in IDIOMAS) + ")",
                name="CK_FALHAS_IDIOMA_FALHA",
            ),
            comment="Códigos de falha e alarme por família e firmware",
        )
        op.create_index("IX_FALHAS_ID_FAMILIA", "FALHAS", ["ID_FAMILIA"])
        op.create_index("IX_FALHAS_CODIGO", "FALHAS", ["CODIGO"])
        op.execute(
            """
            CREATE UNIQUE INDEX "UK_FALHAS_ESCOPO"
            ON "FALHAS" (
                "ID_FAMILIA",
                lower("CODIGO"),
                "IDIOMA",
                COALESCE("VERSAO_FIRMWARE", '')
            )
            """
        )


def downgrade() -> None:
    if not _nao_existe("FALHAS"):
        op.drop_index("UK_FALHAS_ESCOPO", table_name="FALHAS")
        op.drop_index("IX_FALHAS_CODIGO", table_name="FALHAS")
        op.drop_index("IX_FALHAS_ID_FAMILIA", table_name="FALHAS")
        op.drop_table("FALHAS")
    if not _nao_existe("PARAMETROS"):
        op.drop_index("UK_PARAMETROS_ESCOPO", table_name="PARAMETROS")
        op.drop_index("IX_PARAMETROS_CODIGO", table_name="PARAMETROS")
        op.drop_index("IX_PARAMETROS_ID_FAMILIA", table_name="PARAMETROS")
        op.drop_table("PARAMETROS")
