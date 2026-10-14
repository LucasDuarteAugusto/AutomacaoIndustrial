from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Base


class RepositorioBase[M: Base]:
    modelo: type[M]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def obter(self, id_: UUID) -> M | None:
        return await self.session.get(self.modelo, id_)

    async def obter_varios(self, ids: Sequence[UUID]) -> list[M]:
        if not ids:
            return []
        pk = self.modelo.__mapper__.primary_key[0]
        resultado = await self.session.scalars(select(self.modelo).where(pk.in_(ids)))
        return list(resultado.all())

    async def paginar(
        self,
        filtros: Sequence[ColumnElement[bool]],
        ordem: Sequence[Any],
        limit: int,
        offset: int,
    ) -> tuple[list[M], int]:
        total = await self.session.scalar(select(func.count()).select_from(self.modelo).where(*filtros))
        consulta = select(self.modelo).where(*filtros).order_by(*ordem).limit(limit).offset(offset)
        itens = await self.session.scalars(consulta)
        return list(itens.all()), total or 0

    async def existe(self, *filtros: ColumnElement[bool]) -> bool:
        encontrado = await self.session.scalar(select(select(self.modelo).where(*filtros).exists()))
        return bool(encontrado)

    async def adicionar(self, objeto: M) -> M:
        self.session.add(objeto)
        await self.session.flush()
        return objeto

    async def remover(self, objeto: M) -> None:
        await self.session.delete(objeto)
        await self.session.flush()
