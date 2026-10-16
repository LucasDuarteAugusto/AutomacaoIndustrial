from enum import StrEnum
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import UUID_PADRAO, Base, TimestampMixin
from app.documentos.models import Idioma, _enum_varchar


class TipoFalha(StrEnum):
    FALHA = "FALHA"
    ALARME = "ALARME"


class Falha(TimestampMixin, Base):
    __tablename__ = "FALHAS"
    __table_args__ = ({"comment": "Códigos de falha e alarme por família e firmware"},)

    id_falha: Mapped[UUID] = mapped_column(
        "ID_FALHA", primary_key=True, server_default=UUID_PADRAO, comment="Identificador da falha/alarme"
    )
    id_familia: Mapped[UUID] = mapped_column(
        "ID_FAMILIA",
        ForeignKey("FAMILIAS.ID_FAMILIA", ondelete="RESTRICT"),
        index=True,
        comment="Família à qual o código pertence",
    )
    versao_firmware: Mapped[str | None] = mapped_column(
        "VERSAO_FIRMWARE",
        String(30),
        comment="Firmware alvo; nulo = vale para qualquer versão",
    )
    codigo: Mapped[str] = mapped_column("CODIGO", String(40), index=True, comment="Código (ex.: F07801, A0503)")
    tipo: Mapped[TipoFalha] = mapped_column(
        "TIPO",
        _enum_varchar(TipoFalha, "TIPO_FALHA", 20),
        comment="FALHA ou ALARME",
    )
    titulo: Mapped[str] = mapped_column("TITULO", String(200), comment="Nome curto do evento")
    descricao: Mapped[str | None] = mapped_column("DESCRICAO", Text, comment="Descrição detalhada")
    causa: Mapped[str | None] = mapped_column("CAUSA", Text, comment="Causa provável")
    solucao: Mapped[str | None] = mapped_column("SOLUCAO", Text, comment="Ação corretiva recomendada")
    reacao: Mapped[str | None] = mapped_column("REACAO", String(50), comment="Reação do equipamento (parada, aviso, …)")
    idioma: Mapped[Idioma] = mapped_column(
        "IDIOMA",
        _enum_varchar(Idioma, "IDIOMA_FALHA", 5),
        comment="Idioma do texto (pt-BR, en)",
    )
    id_documento: Mapped[UUID | None] = mapped_column(
        "ID_DOCUMENTO",
        ForeignKey("DOCUMENTOS.ID_DOCUMENTO", ondelete="SET NULL"),
        comment="Documento de origem, se houver",
    )
    pagina: Mapped[int | None] = mapped_column("PAGINA", Integer, comment="Página de origem no documento")
    ativo: Mapped[bool] = mapped_column("ATIVO", server_default=true(), comment="Registro disponível para consulta")
