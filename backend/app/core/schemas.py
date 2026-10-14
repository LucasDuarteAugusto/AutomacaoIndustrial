from dataclasses import dataclass
from decimal import Decimal
from typing import Annotated

from fastapi import Depends, Query
from pydantic import AfterValidator, BaseModel, ConfigDict, PlainSerializer

LIMITE_MAXIMO = 100

DecimalJson = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


class Entrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class Saida(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Pagina[T](BaseModel):
    items: list[T]
    total: int


@dataclass(frozen=True)
class Paginacao:
    limit: int
    offset: int


def paginacao(
    limit: Annotated[int, Query(ge=1, le=LIMITE_MAXIMO, description="Itens por página")] = 20,
    offset: Annotated[int, Query(ge=0, description="Quantidade de itens a pular")] = 0,
) -> Paginacao:
    return Paginacao(limit=limit, offset=offset)


PaginacaoDep = Annotated[Paginacao, Depends(paginacao)]


def rejeitar_nulo[V](valor: V | None) -> V:
    if valor is None:
        raise ValueError("não pode ser nulo")
    return valor


NaoNulo = AfterValidator(rejeitar_nulo)
