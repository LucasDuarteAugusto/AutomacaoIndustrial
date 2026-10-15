"""cria_trechos

Create Date: 2026-10-15 16:30:00.000000
"""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import TSVECTOR

revision: str = "c4e8f1a92b07"
down_revision: str | Sequence[str] | None = "add24d28b1b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID_PADRAO = sa.text("gen_random_uuid()")
TIPOS_CONTEUDO = ("TEXTO", "TABELA", "LISTA", "LEGENDA_FIGURA", "CODIGO")
EMBEDDING_DIMENSAO = 1024


def _nao_existe(tabela: str) -> bool:
    return not sa.inspect(op.get_bind()).has_table(tabela)


def _pk(nome: str, comentario: str) -> sa.Column[Any]:
    return sa.Column(nome, sa.Uuid(), server_default=UUID_PADRAO, nullable=False, comment=comentario)


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


def upgrade() -> None:
    if _nao_existe("TRECHOS"):
        op.create_table(
            "TRECHOS",
            _pk("ID_TRECHO", "Identificador do trecho"),
            sa.Column(
                "ID_DOCUMENTO",
                sa.Uuid(),
                sa.ForeignKey("DOCUMENTOS.ID_DOCUMENTO", name="FK_TRECHOS_ID_DOCUMENTO_DOCUMENTOS", ondelete="CASCADE"),
                nullable=False,
                comment="Documento de origem do trecho",
            ),
            sa.Column("ORDEM", sa.Integer(), nullable=False, comment="Ordem do trecho dentro do documento (0-based)"),
            sa.Column("CONTEUDO", sa.Text(), nullable=False, comment="Texto do trecho indexado"),
            sa.Column("SECAO", sa.Text(), nullable=True, comment="Título/caminho da seção no documento"),
            sa.Column("PAGINA", sa.Integer(), nullable=True, comment="Número da página de origem"),
            sa.Column(
                "TIPO_CONTEUDO",
                sa.String(30),
                nullable=False,
                server_default="TEXTO",
                comment="Natureza do trecho (TEXTO, TABELA, LISTA, LEGENDA_FIGURA, CODIGO)",
            ),
            sa.Column(
                "EMBEDDING",
                Vector(EMBEDDING_DIMENSAO),
                nullable=True,
                comment=f"Vetor semântico ({EMBEDDING_DIMENSAO} dimensões; Voyage voyage-context-4)",
            ),
            sa.Column(
                "CONTEUDO_BUSCA",
                TSVECTOR(),
                nullable=True,
                comment="Representação tsvector do CONTEUDO para busca textual híbrida",
            ),
            *_timestamps(),
            sa.PrimaryKeyConstraint("ID_TRECHO", name="PK_TRECHOS"),
            sa.UniqueConstraint("ID_DOCUMENTO", "ORDEM", name="UK_TRECHOS_ID_DOCUMENTO_ORDEM"),
            sa.CheckConstraint(
                '"TIPO_CONTEUDO" IN (' + ", ".join(f"'{v}'" for v in TIPOS_CONTEUDO) + ")",
                name="CK_TRECHOS_TIPO_CONTEUDO",
            ),
            comment="Trechos de documentos com embedding e busca textual",
        )
        op.create_index("IDX_TRECHOS_ID_DOCUMENTO", "TRECHOS", ["ID_DOCUMENTO"])
        op.execute(
            sa.text('CREATE INDEX "IDX_TRECHOS_EMBEDDING_HNSW" ON "TRECHOS" USING hnsw ("EMBEDDING" vector_cosine_ops)')
        )
        op.execute(sa.text('CREATE INDEX "IDX_TRECHOS_CONTEUDO_BUSCA" ON "TRECHOS" USING gin ("CONTEUDO_BUSCA")'))


def downgrade() -> None:
    if not _nao_existe("TRECHOS"):
        op.drop_table("TRECHOS")
