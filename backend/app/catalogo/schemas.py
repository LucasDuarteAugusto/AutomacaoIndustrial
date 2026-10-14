from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import Field

from app.core.schemas import DecimalJson, Entrada, NaoNulo, Saida


class TipoEquipamentoOut(Saida):
    id_tipo_equipamento: UUID
    codigo: str
    nome: str
    descricao: str | None


class FabricanteCreate(Entrada):
    nome: str = Field(min_length=1, max_length=100)
    site: str | None = Field(default=None, max_length=255)
    ativo: bool = True


class FabricanteUpdate(Entrada):
    nome: Annotated[str | None, NaoNulo] = Field(default=None, min_length=1, max_length=100)
    site: str | None = Field(default=None, max_length=255)
    ativo: Annotated[bool | None, NaoNulo] = None


class FabricanteOut(Saida):
    id_fabricante: UUID
    nome: str
    site: str | None
    ativo: bool
    created_at: datetime
    updated_at: datetime


class FamiliaCreate(Entrada):
    id_fabricante: UUID
    id_tipo_equipamento: UUID
    nome: str = Field(min_length=1, max_length=150)
    descricao: str | None = None
    ativo: bool = True


class FamiliaUpdate(Entrada):
    id_fabricante: Annotated[UUID | None, NaoNulo] = None
    id_tipo_equipamento: Annotated[UUID | None, NaoNulo] = None
    nome: Annotated[str | None, NaoNulo] = Field(default=None, min_length=1, max_length=150)
    descricao: str | None = None
    ativo: Annotated[bool | None, NaoNulo] = None


class FamiliaOut(Saida):
    id_familia: UUID
    id_fabricante: UUID
    id_tipo_equipamento: UUID
    nome: str
    descricao: str | None
    ativo: bool
    created_at: datetime
    updated_at: datetime


class FamiliaResumo(Saida):
    id_familia: UUID
    nome: str


class EquipamentoCreate(Entrada):
    id_familia: UUID
    codigo_pedido: str = Field(min_length=1, max_length=60)
    nome: str = Field(min_length=1, max_length=200)
    potencia_kw: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=3)
    tensao_nominal_v: int | None = Field(default=None, ge=0, le=100_000)
    corrente_nominal_a: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=3)
    ativo: bool = True


class EquipamentoUpdate(Entrada):
    id_familia: Annotated[UUID | None, NaoNulo] = None
    codigo_pedido: Annotated[str | None, NaoNulo] = Field(default=None, min_length=1, max_length=60)
    nome: Annotated[str | None, NaoNulo] = Field(default=None, min_length=1, max_length=200)
    potencia_kw: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=3)
    tensao_nominal_v: int | None = Field(default=None, ge=0, le=100_000)
    corrente_nominal_a: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=3)
    ativo: Annotated[bool | None, NaoNulo] = None


class EquipamentoOut(Saida):
    id_equipamento: UUID
    id_familia: UUID
    codigo_pedido: str
    nome: str
    potencia_kw: DecimalJson | None
    tensao_nominal_v: int | None
    corrente_nominal_a: DecimalJson | None
    ativo: bool
    created_at: datetime
    updated_at: datetime


class EquipamentoResumo(Saida):
    id_equipamento: UUID
    codigo_pedido: str
    nome: str
