from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, false, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import UUID_PADRAO, Base, TimestampMixin
from app.documentos.models import Idioma, _enum_varchar


class Parametro(TimestampMixin, Base):
    __tablename__ = "PARAMETROS"
    __table_args__ = ({"comment": "Parâmetros estruturados de comissionamento por família e firmware"},)

    id_parametro: Mapped[UUID] = mapped_column(
        "ID_PARAMETRO", primary_key=True, server_default=UUID_PADRAO, comment="Identificador do parâmetro"
    )
    id_familia: Mapped[UUID] = mapped_column(
        "ID_FAMILIA",
        ForeignKey("FAMILIAS.ID_FAMILIA", ondelete="RESTRICT"),
        index=True,
        comment="Família à qual o parâmetro pertence",
    )
    versao_firmware: Mapped[str | None] = mapped_column(
        "VERSAO_FIRMWARE",
        String(30),
        comment="Firmware alvo; nulo = vale para qualquer versão",
    )
    codigo: Mapped[str] = mapped_column(
        "CODIGO", String(40), index=True, comment="Código do parâmetro (ex.: p1120, P0100)"
    )
    nome: Mapped[str | None] = mapped_column("NOME", String(200), comment="Nome curto / rótulo de menu")
    descricao: Mapped[str] = mapped_column("DESCRICAO", Text, comment="Descrição técnica do parâmetro")
    unidade: Mapped[str | None] = mapped_column("UNIDADE", String(30), comment="Unidade (s, Hz, A, %, …)")
    valor_min: Mapped[Decimal | None] = mapped_column(
        "VALOR_MIN", Numeric(18, 6), comment="Limite inferior numérico, se aplicável"
    )
    valor_max: Mapped[Decimal | None] = mapped_column(
        "VALOR_MAX", Numeric(18, 6), comment="Limite superior numérico, se aplicável"
    )
    valor_padrao: Mapped[str | None] = mapped_column(
        "VALOR_PADRAO", String(100), comment="Valor de fábrica (texto; pode ser enum)"
    )
    grupo: Mapped[str | None] = mapped_column("GRUPO", String(80), comment="Grupo/menu no equipamento")
    somente_leitura: Mapped[bool] = mapped_column(
        "SOMENTE_LEITURA", Boolean, server_default=false(), comment="Parâmetro não editável no equipamento"
    )
    idioma: Mapped[Idioma] = mapped_column(
        "IDIOMA",
        _enum_varchar(Idioma, "IDIOMA_PARAMETRO", 5),
        comment="Idioma do texto (pt-BR, en)",
    )
    id_documento: Mapped[UUID | None] = mapped_column(
        "ID_DOCUMENTO",
        ForeignKey("DOCUMENTOS.ID_DOCUMENTO", ondelete="SET NULL"),
        comment="Documento de origem (lista de parâmetros), se houver",
    )
    pagina: Mapped[int | None] = mapped_column("PAGINA", Integer, comment="Página de origem no documento")
    ativo: Mapped[bool] = mapped_column("ATIVO", server_default=true(), comment="Registro disponível para consulta")
