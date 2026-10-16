from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import Field

from app.core.schemas import DecimalJson, Entrada, NaoNulo, Saida
from app.documentos.models import Idioma


class ParametroCreate(Entrada):
    id_familia: UUID
    codigo: str = Field(min_length=1, max_length=40)
    descricao: str = Field(min_length=1)
    idioma: Idioma = Idioma.PT_BR
    versao_firmware: str | None = Field(default=None, max_length=30)
    nome: str | None = Field(default=None, max_length=200)
    unidade: str | None = Field(default=None, max_length=30)
    valor_min: Decimal | None = Field(default=None, max_digits=18, decimal_places=6)
    valor_max: Decimal | None = Field(default=None, max_digits=18, decimal_places=6)
    valor_padrao: str | None = Field(default=None, max_length=100)
    grupo: str | None = Field(default=None, max_length=80)
    somente_leitura: bool = False
    id_documento: UUID | None = None
    pagina: int | None = Field(default=None, ge=1)
    ativo: bool = True


class ParametroUpdate(Entrada):
    id_familia: Annotated[UUID | None, NaoNulo] = None
    codigo: Annotated[str | None, NaoNulo] = Field(default=None, min_length=1, max_length=40)
    descricao: Annotated[str | None, NaoNulo] = Field(default=None, min_length=1)
    idioma: Annotated[Idioma | None, NaoNulo] = None
    versao_firmware: str | None = Field(default=None, max_length=30)
    nome: str | None = Field(default=None, max_length=200)
    unidade: str | None = Field(default=None, max_length=30)
    valor_min: Decimal | None = Field(default=None, max_digits=18, decimal_places=6)
    valor_max: Decimal | None = Field(default=None, max_digits=18, decimal_places=6)
    valor_padrao: str | None = Field(default=None, max_length=100)
    grupo: str | None = Field(default=None, max_length=80)
    somente_leitura: Annotated[bool | None, NaoNulo] = None
    id_documento: UUID | None = None
    pagina: int | None = Field(default=None, ge=1)
    ativo: Annotated[bool | None, NaoNulo] = None


class ParametroOut(Saida):
    id_parametro: UUID
    id_familia: UUID
    versao_firmware: str | None
    codigo: str
    nome: str | None
    descricao: str
    unidade: str | None
    valor_min: DecimalJson | None
    valor_max: DecimalJson | None
    valor_padrao: str | None
    grupo: str | None
    somente_leitura: bool
    idioma: Idioma
    id_documento: UUID | None
    pagina: int | None
    ativo: bool
    created_at: datetime
    updated_at: datetime
