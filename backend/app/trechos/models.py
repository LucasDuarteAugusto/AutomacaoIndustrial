from enum import StrEnum
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import UUID_PADRAO, Base, TimestampMixin
from app.core.ia_defaults import EMBEDDING_DIMENSAO_PADRAO


class TipoConteudo(StrEnum):
    TEXTO = "TEXTO"
    TABELA = "TABELA"
    LISTA = "LISTA"
    LEGENDA_FIGURA = "LEGENDA_FIGURA"
    CODIGO = "CODIGO"


def _enum_varchar(enum: type[StrEnum], nome: str, tamanho: int) -> Enum:
    return Enum(
        enum,
        name=nome,
        native_enum=False,
        create_constraint=True,
        length=tamanho,
        values_callable=lambda membros: [m.value for m in membros],
    )


class Trecho(TimestampMixin, Base):
    __tablename__ = "TRECHOS"
    __table_args__ = (
        UniqueConstraint("ID_DOCUMENTO", "ORDEM"),
        {"comment": "Trechos de documentos com embedding e busca textual"},
    )

    id_trecho: Mapped[UUID] = mapped_column(
        "ID_TRECHO", primary_key=True, server_default=UUID_PADRAO, comment="Identificador do trecho"
    )
    id_documento: Mapped[UUID] = mapped_column(
        "ID_DOCUMENTO",
        ForeignKey("DOCUMENTOS.ID_DOCUMENTO", ondelete="CASCADE"),
        index=True,
        comment="Documento de origem do trecho",
    )
    ordem: Mapped[int] = mapped_column("ORDEM", Integer, comment="Ordem do trecho dentro do documento (0-based)")
    conteudo: Mapped[str] = mapped_column("CONTEUDO", Text, comment="Texto do trecho indexado")
    secao: Mapped[str | None] = mapped_column("SECAO", Text, comment="Título/caminho da seção no documento")
    pagina: Mapped[int | None] = mapped_column("PAGINA", Integer, comment="Número da página de origem")
    tipo_conteudo: Mapped[TipoConteudo] = mapped_column(
        "TIPO_CONTEUDO",
        _enum_varchar(TipoConteudo, "TIPO_CONTEUDO", 30),
        default=TipoConteudo.TEXTO,
        server_default=TipoConteudo.TEXTO.value,
        comment="Natureza do trecho (TEXTO, TABELA, LISTA, LEGENDA_FIGURA, CODIGO)",
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        "EMBEDDING",
        Vector(EMBEDDING_DIMENSAO_PADRAO),
        nullable=True,
        comment=f"Vetor semântico ({EMBEDDING_DIMENSAO_PADRAO} dimensões; Voyage voyage-context-4)",
    )
    conteudo_busca: Mapped[str | None] = mapped_column(
        "CONTEUDO_BUSCA",
        TSVECTOR(),
        nullable=True,
        comment="Representação tsvector do CONTEUDO para busca textual híbrida",
    )
