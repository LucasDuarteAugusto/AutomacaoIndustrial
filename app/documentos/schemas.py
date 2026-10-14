from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field

from app.catalogo.schemas import EquipamentoResumo, FamiliaResumo
from app.core.schemas import Entrada, NaoNulo, Saida
from app.documentos.models import Idioma, StatusProcessamento, TipoDocumento


class DocumentoCreate(Entrada):
    titulo: str = Field(min_length=1, max_length=300)
    tipo_documento: TipoDocumento
    idioma: Idioma
    codigo_documento: str | None = Field(default=None, max_length=60)
    edicao: str | None = Field(default=None, max_length=30)
    versao_firmware: str | None = Field(default=None, max_length=30)
    ids_familias: list[UUID] = Field(min_length=1, description="Famílias cobertas (pelo menos uma)")
    ids_equipamentos: list[UUID] = Field(default_factory=list, description="Modelos específicos (opcional)")


class DocumentoUpdate(Entrada):
    titulo: Annotated[str | None, NaoNulo] = Field(default=None, min_length=1, max_length=300)
    tipo_documento: Annotated[TipoDocumento | None, NaoNulo] = None
    idioma: Annotated[Idioma | None, NaoNulo] = None
    codigo_documento: str | None = Field(default=None, max_length=60)
    edicao: str | None = Field(default=None, max_length=30)
    versao_firmware: str | None = Field(default=None, max_length=30)
    ids_familias: Annotated[list[UUID] | None, NaoNulo] = Field(default=None, min_length=1)
    ids_equipamentos: Annotated[list[UUID] | None, NaoNulo] = None


class DocumentoOut(Saida):
    id_documento: UUID
    titulo: str
    tipo_documento: TipoDocumento
    idioma: Idioma
    codigo_documento: str | None
    edicao: str | None
    versao_firmware: str | None
    chave_arquivo: str | None
    hash_sha256: str | None
    tamanho_bytes: int | None
    paginas: int | None
    status_processamento: StatusProcessamento
    erro_processamento: str | None
    familias: list[FamiliaResumo]
    equipamentos: list[EquipamentoResumo]
    created_at: datetime
    updated_at: datetime
