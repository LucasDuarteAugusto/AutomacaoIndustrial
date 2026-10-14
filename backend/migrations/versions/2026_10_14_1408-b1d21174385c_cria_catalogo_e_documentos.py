"""cria_catalogo_e_documentos

Create Date: 2026-10-14 14:08:31.470412
"""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "b1d21174385c"
down_revision: str | Sequence[str] | None = "6a9c15cafac3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID_PADRAO = sa.text("gen_random_uuid()")

TIPOS_DOCUMENTO = (
    "MANUAL_OPERACAO",
    "LISTA_PARAMETROS",
    "GUIA_RAPIDO",
    "MANUAL_COMUNICACAO",
    "DATASHEET",
    "NOTA_APLICACAO",
)
IDIOMAS = ("pt-BR", "en")
STATUS_PROCESSAMENTO = ("PENDENTE", "PROCESSANDO", "INDEXADO", "ERRO")


def _nao_existe(tabela: str) -> bool:
    return not sa.inspect(op.get_bind()).has_table(tabela)


def _pk(nome: str, comentario: str) -> sa.Column[Any]:
    return sa.Column(nome, sa.Uuid(), server_default=UUID_PADRAO, nullable=False, comment=comentario)


def _ativo(comentario: str) -> sa.Column[Any]:
    return sa.Column("ATIVO", sa.Boolean(), server_default=sa.true(), nullable=False, comment=comentario)


def _timestamps() -> list[sa.Column[Any]]:
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


def _check_in(coluna: str, valores: Sequence[str], nome: str) -> sa.CheckConstraint:
    lista = ", ".join(f"'{v}'" for v in valores)
    return sa.CheckConstraint(f'"{coluna}" IN ({lista})', name=nome)


def upgrade() -> None:
    if _nao_existe("TIPOS_EQUIPAMENTO"):
        op.create_table(
            "TIPOS_EQUIPAMENTO",
            _pk("ID_TIPO_EQUIPAMENTO", "Identificador do tipo"),
            sa.Column(
                "CODIGO",
                sa.String(40),
                nullable=False,
                comment="Código estável do tipo (ex.: INVERSOR, SOFT_STARTER)",
            ),
            sa.Column("NOME", sa.String(100), nullable=False, comment="Nome de exibição do tipo"),
            sa.Column("DESCRICAO", sa.Text(), nullable=True, comment="Descrição do tipo de equipamento"),
            *_timestamps(),
            sa.PrimaryKeyConstraint("ID_TIPO_EQUIPAMENTO", name="PK_TIPOS_EQUIPAMENTO"),
            sa.UniqueConstraint("CODIGO", name="UK_TIPOS_EQUIPAMENTO_CODIGO"),
            comment="Categorias de equipamento de acionamento de motores",
        )

    if _nao_existe("FABRICANTES"):
        op.create_table(
            "FABRICANTES",
            _pk("ID_FABRICANTE", "Identificador do fabricante"),
            sa.Column("NOME", sa.String(100), nullable=False, comment="Nome do fabricante (ex.: Siemens)"),
            sa.Column("SITE", sa.String(255), nullable=True, comment="Site oficial do fabricante"),
            _ativo("Fabricante disponível para uso"),
            *_timestamps(),
            sa.PrimaryKeyConstraint("ID_FABRICANTE", name="PK_FABRICANTES"),
            sa.UniqueConstraint("NOME", name="UK_FABRICANTES_NOME"),
            comment="Fabricantes de equipamentos de acionamento",
        )

    if _nao_existe("FAMILIAS"):
        op.create_table(
            "FAMILIAS",
            _pk("ID_FAMILIA", "Identificador da família"),
            sa.Column("ID_FABRICANTE", sa.Uuid(), nullable=False, comment="Fabricante da família"),
            sa.Column("ID_TIPO_EQUIPAMENTO", sa.Uuid(), nullable=False, comment="Tipo de equipamento da família"),
            sa.Column("NOME", sa.String(150), nullable=False, comment="Nome da família, único por fabricante"),
            sa.Column("DESCRICAO", sa.Text(), nullable=True, comment="Descrição da família"),
            _ativo("Família disponível para uso"),
            *_timestamps(),
            sa.ForeignKeyConstraint(
                ["ID_FABRICANTE"],
                ["FABRICANTES.ID_FABRICANTE"],
                name="FK_FAMILIAS_ID_FABRICANTE_FABRICANTES",
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["ID_TIPO_EQUIPAMENTO"],
                ["TIPOS_EQUIPAMENTO.ID_TIPO_EQUIPAMENTO"],
                name="FK_FAMILIAS_ID_TIPO_EQUIPAMENTO_TIPOS_EQUIPAMENTO",
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("ID_FAMILIA", name="PK_FAMILIAS"),
            sa.UniqueConstraint("ID_FABRICANTE", "NOME", name="UK_FAMILIAS_ID_FABRICANTE_NOME"),
            comment="Linhas de produto de um fabricante (ex.: SINAMICS G120, SIRIUS 3RW55)",
        )
        op.create_index("IDX_FAMILIAS_ID_TIPO_EQUIPAMENTO", "FAMILIAS", ["ID_TIPO_EQUIPAMENTO"])

    if _nao_existe("EQUIPAMENTOS"):
        op.create_table(
            "EQUIPAMENTOS",
            _pk("ID_EQUIPAMENTO", "Identificador do equipamento"),
            sa.Column("ID_FAMILIA", sa.Uuid(), nullable=False, comment="Família do equipamento"),
            sa.Column(
                "CODIGO_PEDIDO",
                sa.String(60),
                nullable=False,
                comment="Código de pedido do fabricante (MLFB), único por família",
            ),
            sa.Column("NOME", sa.String(200), nullable=False, comment="Nome comercial do modelo"),
            sa.Column("POTENCIA_KW", sa.Numeric(10, 3), nullable=True, comment="Potência nominal do motor em kW"),
            sa.Column("TENSAO_NOMINAL_V", sa.Integer(), nullable=True, comment="Tensão nominal em V"),
            sa.Column("CORRENTE_NOMINAL_A", sa.Numeric(10, 3), nullable=True, comment="Corrente nominal em A"),
            _ativo("Equipamento disponível para uso"),
            *_timestamps(),
            sa.ForeignKeyConstraint(
                ["ID_FAMILIA"],
                ["FAMILIAS.ID_FAMILIA"],
                name="FK_EQUIPAMENTOS_ID_FAMILIA_FAMILIAS",
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("ID_EQUIPAMENTO", name="PK_EQUIPAMENTOS"),
            sa.UniqueConstraint("ID_FAMILIA", "CODIGO_PEDIDO", name="UK_EQUIPAMENTOS_ID_FAMILIA_CODIGO_PEDIDO"),
            comment="Modelos específicos de equipamento, identificados pelo código de pedido",
        )

    if _nao_existe("DOCUMENTOS"):
        op.create_table(
            "DOCUMENTOS",
            _pk("ID_DOCUMENTO", "Identificador do documento"),
            sa.Column("TITULO", sa.String(300), nullable=False, comment="Título do documento"),
            sa.Column("TIPO_DOCUMENTO", sa.String(30), nullable=False, comment="Tipo do documento"),
            sa.Column("IDIOMA", sa.String(5), nullable=False, comment="Idioma do documento (pt-BR, en)"),
            sa.Column(
                "CODIGO_DOCUMENTO",
                sa.String(60),
                nullable=True,
                comment="Número do documento no fabricante (ex.: A5E33840768)",
            ),
            sa.Column("EDICAO", sa.String(30), nullable=True, comment="Edição do documento (ex.: 09/2023)"),
            sa.Column(
                "VERSAO_FIRMWARE",
                sa.String(30),
                nullable=True,
                comment="Versão de firmware a que o documento se aplica",
            ),
            sa.Column(
                "CHAVE_ARQUIVO",
                sa.String(500),
                nullable=True,
                comment="Caminho/chave do PDF no armazenamento de arquivos",
            ),
            sa.Column(
                "HASH_SHA256", sa.String(64), nullable=True, comment="Hash SHA-256 do arquivo; evita duplicidade"
            ),
            sa.Column("TAMANHO_BYTES", sa.Integer(), nullable=True, comment="Tamanho do arquivo em bytes"),
            sa.Column("PAGINAS", sa.Integer(), nullable=True, comment="Quantidade de páginas"),
            sa.Column(
                "STATUS_PROCESSAMENTO",
                sa.String(20),
                server_default="PENDENTE",
                nullable=False,
                comment="Etapa da ingestão (PENDENTE, PROCESSANDO, INDEXADO, ERRO)",
            ),
            sa.Column("ERRO_PROCESSAMENTO", sa.Text(), nullable=True, comment="Mensagem de erro da última ingestão"),
            *_timestamps(),
            _check_in("TIPO_DOCUMENTO", TIPOS_DOCUMENTO, "CK_DOCUMENTOS_TIPO_DOCUMENTO"),
            _check_in("IDIOMA", IDIOMAS, "CK_DOCUMENTOS_IDIOMA"),
            _check_in("STATUS_PROCESSAMENTO", STATUS_PROCESSAMENTO, "CK_DOCUMENTOS_STATUS_PROCESSAMENTO"),
            sa.PrimaryKeyConstraint("ID_DOCUMENTO", name="PK_DOCUMENTOS"),
            sa.UniqueConstraint("HASH_SHA256", name="UK_DOCUMENTOS_HASH_SHA256"),
            comment="Documentos técnicos (manuais, listas de parâmetros, datasheets)",
        )

    if _nao_existe("DOCUMENTOS_FAMILIAS"):
        op.create_table(
            "DOCUMENTOS_FAMILIAS",
            _pk("ID_DOCUMENTO_FAMILIA", "Identificador do vínculo"),
            sa.Column("ID_DOCUMENTO", sa.Uuid(), nullable=False, comment="Documento vinculado"),
            sa.Column("ID_FAMILIA", sa.Uuid(), nullable=False, comment="Família coberta pelo documento"),
            *_timestamps(),
            sa.ForeignKeyConstraint(
                ["ID_DOCUMENTO"],
                ["DOCUMENTOS.ID_DOCUMENTO"],
                name="FK_DOCUMENTOS_FAMILIAS_ID_DOCUMENTO_DOCUMENTOS",
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["ID_FAMILIA"],
                ["FAMILIAS.ID_FAMILIA"],
                name="FK_DOCUMENTOS_FAMILIAS_ID_FAMILIA_FAMILIAS",
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("ID_DOCUMENTO_FAMILIA", name="PK_DOCUMENTOS_FAMILIAS"),
            sa.UniqueConstraint("ID_DOCUMENTO", "ID_FAMILIA", name="UK_DOCUMENTOS_FAMILIAS_ID_DOCUMENTO_ID_FAMILIA"),
            comment="Vínculo N:N entre documentos e as famílias que eles cobrem",
        )
        op.create_index("IDX_DOCUMENTOS_FAMILIAS_ID_FAMILIA", "DOCUMENTOS_FAMILIAS", ["ID_FAMILIA"])

    if _nao_existe("DOCUMENTOS_EQUIPAMENTOS"):
        op.create_table(
            "DOCUMENTOS_EQUIPAMENTOS",
            _pk("ID_DOCUMENTO_EQUIPAMENTO", "Identificador do vínculo"),
            sa.Column("ID_DOCUMENTO", sa.Uuid(), nullable=False, comment="Documento vinculado"),
            sa.Column("ID_EQUIPAMENTO", sa.Uuid(), nullable=False, comment="Equipamento coberto pelo documento"),
            *_timestamps(),
            sa.ForeignKeyConstraint(
                ["ID_DOCUMENTO"],
                ["DOCUMENTOS.ID_DOCUMENTO"],
                name="FK_DOCUMENTOS_EQUIPAMENTOS_ID_DOCUMENTO_DOCUMENTOS",
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["ID_EQUIPAMENTO"],
                ["EQUIPAMENTOS.ID_EQUIPAMENTO"],
                name="FK_DOCUMENTOS_EQUIPAMENTOS_ID_EQUIPAMENTO_EQUIPAMENTOS",
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("ID_DOCUMENTO_EQUIPAMENTO", name="PK_DOCUMENTOS_EQUIPAMENTOS"),
            sa.UniqueConstraint(
                "ID_DOCUMENTO", "ID_EQUIPAMENTO", name="UK_DOCUMENTOS_EQUIPAMENTOS_ID_DOCUMENTO_ID_EQUIPAMENTO"
            ),
            comment="Vínculo N:N opcional entre documentos e modelos específicos",
        )
        op.create_index("IDX_DOCUMENTOS_EQUIPAMENTOS_ID_EQUIPAMENTO", "DOCUMENTOS_EQUIPAMENTOS", ["ID_EQUIPAMENTO"])


def downgrade() -> None:
    op.drop_index("IDX_DOCUMENTOS_EQUIPAMENTOS_ID_EQUIPAMENTO", table_name="DOCUMENTOS_EQUIPAMENTOS")
    op.drop_table("DOCUMENTOS_EQUIPAMENTOS")
    op.drop_index("IDX_DOCUMENTOS_FAMILIAS_ID_FAMILIA", table_name="DOCUMENTOS_FAMILIAS")
    op.drop_table("DOCUMENTOS_FAMILIAS")
    op.drop_table("DOCUMENTOS")
    op.drop_table("EQUIPAMENTOS")
    op.drop_index("IDX_FAMILIAS_ID_TIPO_EQUIPAMENTO", table_name="FAMILIAS")
    op.drop_table("FAMILIAS")
    op.drop_table("FABRICANTES")
    op.drop_table("TIPOS_EQUIPAMENTO")
