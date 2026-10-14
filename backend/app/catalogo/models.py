from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import UUID_PADRAO, Base, TimestampMixin


class TipoEquipamento(TimestampMixin, Base):
    __tablename__ = "TIPOS_EQUIPAMENTO"
    __table_args__ = ({"comment": "Categorias de equipamento de acionamento de motores"},)

    id_tipo_equipamento: Mapped[UUID] = mapped_column(
        "ID_TIPO_EQUIPAMENTO", primary_key=True, server_default=UUID_PADRAO, comment="Identificador do tipo"
    )
    codigo: Mapped[str] = mapped_column(
        "CODIGO", String(40), unique=True, comment="Código estável do tipo (ex.: INVERSOR, SOFT_STARTER)"
    )
    nome: Mapped[str] = mapped_column("NOME", String(100), comment="Nome de exibição do tipo")
    descricao: Mapped[str | None] = mapped_column("DESCRICAO", Text, comment="Descrição do tipo de equipamento")


class Fabricante(TimestampMixin, Base):
    __tablename__ = "FABRICANTES"
    __table_args__ = ({"comment": "Fabricantes de equipamentos de acionamento"},)

    id_fabricante: Mapped[UUID] = mapped_column(
        "ID_FABRICANTE", primary_key=True, server_default=UUID_PADRAO, comment="Identificador do fabricante"
    )
    nome: Mapped[str] = mapped_column("NOME", String(100), unique=True, comment="Nome do fabricante (ex.: Siemens)")
    site: Mapped[str | None] = mapped_column("SITE", String(255), comment="Site oficial do fabricante")
    ativo: Mapped[bool] = mapped_column("ATIVO", server_default=true(), comment="Fabricante disponível para uso")


class Familia(TimestampMixin, Base):
    __tablename__ = "FAMILIAS"
    __table_args__ = (
        UniqueConstraint("ID_FABRICANTE", "NOME"),
        {"comment": "Linhas de produto de um fabricante (ex.: SINAMICS G120, SIRIUS 3RW55)"},
    )

    id_familia: Mapped[UUID] = mapped_column(
        "ID_FAMILIA", primary_key=True, server_default=UUID_PADRAO, comment="Identificador da família"
    )
    id_fabricante: Mapped[UUID] = mapped_column(
        "ID_FABRICANTE",
        ForeignKey("FABRICANTES.ID_FABRICANTE", ondelete="RESTRICT"),
        comment="Fabricante da família",
    )
    id_tipo_equipamento: Mapped[UUID] = mapped_column(
        "ID_TIPO_EQUIPAMENTO",
        ForeignKey("TIPOS_EQUIPAMENTO.ID_TIPO_EQUIPAMENTO", ondelete="RESTRICT"),
        index=True,
        comment="Tipo de equipamento da família",
    )
    nome: Mapped[str] = mapped_column("NOME", String(150), comment="Nome da família, único por fabricante")
    descricao: Mapped[str | None] = mapped_column("DESCRICAO", Text, comment="Descrição da família")
    ativo: Mapped[bool] = mapped_column("ATIVO", server_default=true(), comment="Família disponível para uso")


class Equipamento(TimestampMixin, Base):
    __tablename__ = "EQUIPAMENTOS"
    __table_args__ = (
        UniqueConstraint("ID_FAMILIA", "CODIGO_PEDIDO"),
        {"comment": "Modelos específicos de equipamento, identificados pelo código de pedido"},
    )

    id_equipamento: Mapped[UUID] = mapped_column(
        "ID_EQUIPAMENTO", primary_key=True, server_default=UUID_PADRAO, comment="Identificador do equipamento"
    )
    id_familia: Mapped[UUID] = mapped_column(
        "ID_FAMILIA", ForeignKey("FAMILIAS.ID_FAMILIA", ondelete="RESTRICT"), comment="Família do equipamento"
    )
    codigo_pedido: Mapped[str] = mapped_column(
        "CODIGO_PEDIDO", String(60), comment="Código de pedido do fabricante (MLFB), único por família"
    )
    nome: Mapped[str] = mapped_column("NOME", String(200), comment="Nome comercial do modelo")
    potencia_kw: Mapped[Decimal | None] = mapped_column(
        "POTENCIA_KW", Numeric(10, 3), comment="Potência nominal do motor em kW"
    )
    tensao_nominal_v: Mapped[int | None] = mapped_column("TENSAO_NOMINAL_V", Integer, comment="Tensão nominal em V")
    corrente_nominal_a: Mapped[Decimal | None] = mapped_column(
        "CORRENTE_NOMINAL_A", Numeric(10, 3), comment="Corrente nominal em A"
    )
    ativo: Mapped[bool] = mapped_column("ATIVO", server_default=true(), comment="Equipamento disponível para uso")
