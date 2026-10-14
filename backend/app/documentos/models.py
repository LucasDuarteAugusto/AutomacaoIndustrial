from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.catalogo.models import Equipamento, Familia
from app.core.db import UUID_PADRAO, Base, TimestampMixin


class TipoDocumento(StrEnum):
    MANUAL_OPERACAO = "MANUAL_OPERACAO"
    LISTA_PARAMETROS = "LISTA_PARAMETROS"
    GUIA_RAPIDO = "GUIA_RAPIDO"
    MANUAL_COMUNICACAO = "MANUAL_COMUNICACAO"
    DATASHEET = "DATASHEET"
    NOTA_APLICACAO = "NOTA_APLICACAO"


class Idioma(StrEnum):
    PT_BR = "pt-BR"
    EN = "en"


class StatusProcessamento(StrEnum):
    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    INDEXADO = "INDEXADO"
    ERRO = "ERRO"


def _enum_varchar(enum: type[StrEnum], nome: str, tamanho: int) -> Enum:
    return Enum(
        enum,
        name=nome,
        native_enum=False,
        create_constraint=True,
        length=tamanho,
        values_callable=lambda membros: [m.value for m in membros],
    )


class DocumentoFamilia(TimestampMixin, Base):
    __tablename__ = "DOCUMENTOS_FAMILIAS"
    __table_args__ = (
        UniqueConstraint("ID_DOCUMENTO", "ID_FAMILIA"),
        {"comment": "Vínculo N:N entre documentos e as famílias que eles cobrem"},
    )

    id_documento_familia: Mapped[UUID] = mapped_column(
        "ID_DOCUMENTO_FAMILIA", primary_key=True, server_default=UUID_PADRAO, comment="Identificador do vínculo"
    )
    id_documento: Mapped[UUID] = mapped_column(
        "ID_DOCUMENTO", ForeignKey("DOCUMENTOS.ID_DOCUMENTO", ondelete="CASCADE"), comment="Documento vinculado"
    )
    id_familia: Mapped[UUID] = mapped_column(
        "ID_FAMILIA",
        ForeignKey("FAMILIAS.ID_FAMILIA", ondelete="RESTRICT"),
        index=True,
        comment="Família coberta pelo documento",
    )


class DocumentoEquipamento(TimestampMixin, Base):
    __tablename__ = "DOCUMENTOS_EQUIPAMENTOS"
    __table_args__ = (
        UniqueConstraint("ID_DOCUMENTO", "ID_EQUIPAMENTO"),
        {"comment": "Vínculo N:N opcional entre documentos e modelos específicos"},
    )

    id_documento_equipamento: Mapped[UUID] = mapped_column(
        "ID_DOCUMENTO_EQUIPAMENTO", primary_key=True, server_default=UUID_PADRAO, comment="Identificador do vínculo"
    )
    id_documento: Mapped[UUID] = mapped_column(
        "ID_DOCUMENTO", ForeignKey("DOCUMENTOS.ID_DOCUMENTO", ondelete="CASCADE"), comment="Documento vinculado"
    )
    id_equipamento: Mapped[UUID] = mapped_column(
        "ID_EQUIPAMENTO",
        ForeignKey("EQUIPAMENTOS.ID_EQUIPAMENTO", ondelete="RESTRICT"),
        index=True,
        comment="Equipamento coberto pelo documento",
    )


class Documento(TimestampMixin, Base):
    __tablename__ = "DOCUMENTOS"
    __table_args__ = ({"comment": "Documentos técnicos (manuais, listas de parâmetros, datasheets)"},)

    id_documento: Mapped[UUID] = mapped_column(
        "ID_DOCUMENTO", primary_key=True, server_default=UUID_PADRAO, comment="Identificador do documento"
    )
    titulo: Mapped[str] = mapped_column("TITULO", String(300), comment="Título do documento")
    tipo_documento: Mapped[TipoDocumento] = mapped_column(
        "TIPO_DOCUMENTO", _enum_varchar(TipoDocumento, "TIPO_DOCUMENTO", 30), comment="Tipo do documento"
    )
    idioma: Mapped[Idioma] = mapped_column(
        "IDIOMA", _enum_varchar(Idioma, "IDIOMA", 5), comment="Idioma do documento (pt-BR, en)"
    )
    codigo_documento: Mapped[str | None] = mapped_column(
        "CODIGO_DOCUMENTO", String(60), comment="Número do documento no fabricante (ex.: A5E33840768)"
    )
    edicao: Mapped[str | None] = mapped_column("EDICAO", String(30), comment="Edição do documento (ex.: 09/2023)")
    versao_firmware: Mapped[str | None] = mapped_column(
        "VERSAO_FIRMWARE", String(30), comment="Versão de firmware a que o documento se aplica"
    )
    chave_arquivo: Mapped[str | None] = mapped_column(
        "CHAVE_ARQUIVO", String(500), comment="Caminho/chave do PDF no armazenamento de arquivos"
    )
    hash_sha256: Mapped[str | None] = mapped_column(
        "HASH_SHA256", String(64), unique=True, comment="Hash SHA-256 do arquivo; evita duplicidade"
    )
    tamanho_bytes: Mapped[int | None] = mapped_column("TAMANHO_BYTES", Integer, comment="Tamanho do arquivo em bytes")
    paginas: Mapped[int | None] = mapped_column("PAGINAS", Integer, comment="Quantidade de páginas")
    status_processamento: Mapped[StatusProcessamento] = mapped_column(
        "STATUS_PROCESSAMENTO",
        _enum_varchar(StatusProcessamento, "STATUS_PROCESSAMENTO", 20),
        default=StatusProcessamento.PENDENTE,
        server_default=StatusProcessamento.PENDENTE.value,
        comment="Etapa da ingestão (PENDENTE, PROCESSANDO, INDEXADO, ERRO)",
    )
    erro_processamento: Mapped[str | None] = mapped_column(
        "ERRO_PROCESSAMENTO", Text, comment="Mensagem de erro da última ingestão"
    )

    familias: Mapped[list[Familia]] = relationship(
        secondary="DOCUMENTOS_FAMILIAS", lazy="selectin", order_by=Familia.nome
    )
    equipamentos: Mapped[list[Equipamento]] = relationship(
        secondary="DOCUMENTOS_EQUIPAMENTOS", lazy="selectin", order_by=Equipamento.codigo_pedido
    )
