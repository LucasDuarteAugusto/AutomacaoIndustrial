from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field

from app.core.schemas import Entrada, NaoNulo, Saida
from app.documentos.models import Idioma
from app.falhas.models import TipoFalha


class FalhaCreate(Entrada):
    id_familia: UUID
    codigo: str = Field(min_length=1, max_length=40)
    tipo: TipoFalha
    titulo: str = Field(min_length=1, max_length=200)
    idioma: Idioma = Idioma.PT_BR
    versao_firmware: str | None = Field(default=None, max_length=30)
    descricao: str | None = None
    causa: str | None = None
    solucao: str | None = None
    reacao: str | None = Field(default=None, max_length=50)
    id_documento: UUID | None = None
    pagina: int | None = Field(default=None, ge=1)
    ativo: bool = True


class FalhaUpdate(Entrada):
    id_familia: Annotated[UUID | None, NaoNulo] = None
    codigo: Annotated[str | None, NaoNulo] = Field(default=None, min_length=1, max_length=40)
    tipo: Annotated[TipoFalha | None, NaoNulo] = None
    titulo: Annotated[str | None, NaoNulo] = Field(default=None, min_length=1, max_length=200)
    idioma: Annotated[Idioma | None, NaoNulo] = None
    versao_firmware: str | None = Field(default=None, max_length=30)
    descricao: str | None = None
    causa: str | None = None
    solucao: str | None = None
    reacao: str | None = Field(default=None, max_length=50)
    id_documento: UUID | None = None
    pagina: int | None = Field(default=None, ge=1)
    ativo: Annotated[bool | None, NaoNulo] = None


class FalhaOut(Saida):
    id_falha: UUID
    id_familia: UUID
    versao_firmware: str | None
    codigo: str
    tipo: TipoFalha
    titulo: str
    descricao: str | None
    causa: str | None
    solucao: str | None
    reacao: str | None
    idioma: Idioma
    id_documento: UUID | None
    pagina: int | None
    ativo: bool
    created_at: datetime
    updated_at: datetime
