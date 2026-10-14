from collections.abc import Set

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Base
from app.core.errors import Conflito
from app.core.repository import RepositorioBase


def aplicar_alteracoes(objeto: Base, dados: BaseModel, ignorar: Set[str] = frozenset()) -> None:
    for campo, valor in dados.model_dump(exclude_unset=True, exclude=set(ignorar)).items():
        setattr(objeto, campo, valor)


async def remover_ou_conflito[M: Base](session: AsyncSession, repo: RepositorioBase[M], objeto: M, motivo: str) -> None:
    try:
        await repo.remover(objeto)
    except IntegrityError as erro:
        await session.rollback()
        raise Conflito(motivo) from erro
    await session.commit()
