from typing import Any
from uuid import UUID

from sqlalchemy import ColumnElement, func, or_

from app.catalogo.models import Equipamento, Fabricante, Familia, TipoEquipamento
from app.core.repository import RepositorioBase


def _diferente_de(coluna: Any, id_: UUID | None) -> list[ColumnElement[bool]]:
    return [coluna != id_] if id_ else []


class TipoEquipamentoRepository(RepositorioBase[TipoEquipamento]):
    modelo = TipoEquipamento

    async def listar(self, limit: int, offset: int) -> tuple[list[TipoEquipamento], int]:
        return await self.paginar([], [TipoEquipamento.nome], limit, offset)


class FabricanteRepository(RepositorioBase[Fabricante]):
    modelo = Fabricante

    async def listar(
        self, busca: str | None, ativo: bool | None, limit: int, offset: int
    ) -> tuple[list[Fabricante], int]:
        filtros: list[ColumnElement[bool]] = []
        if busca:
            filtros.append(Fabricante.nome.icontains(busca, autoescape=True))
        if ativo is not None:
            filtros.append(Fabricante.ativo.is_(ativo))
        return await self.paginar(filtros, [Fabricante.nome], limit, offset)

    async def nome_em_uso(self, nome: str, ignorar_id: UUID | None = None) -> bool:
        return await self.existe(
            func.lower(Fabricante.nome) == nome.lower(), *_diferente_de(Fabricante.id_fabricante, ignorar_id)
        )


class FamiliaRepository(RepositorioBase[Familia]):
    modelo = Familia

    async def listar(
        self,
        id_fabricante: UUID | None,
        id_tipo_equipamento: UUID | None,
        busca: str | None,
        ativo: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Familia], int]:
        filtros: list[ColumnElement[bool]] = []
        if id_fabricante:
            filtros.append(Familia.id_fabricante == id_fabricante)
        if id_tipo_equipamento:
            filtros.append(Familia.id_tipo_equipamento == id_tipo_equipamento)
        if busca:
            filtros.append(Familia.nome.icontains(busca, autoescape=True))
        if ativo is not None:
            filtros.append(Familia.ativo.is_(ativo))
        return await self.paginar(filtros, [Familia.nome], limit, offset)

    async def nome_em_uso(self, id_fabricante: UUID, nome: str, ignorar_id: UUID | None = None) -> bool:
        return await self.existe(
            Familia.id_fabricante == id_fabricante,
            func.lower(Familia.nome) == nome.lower(),
            *_diferente_de(Familia.id_familia, ignorar_id),
        )


class EquipamentoRepository(RepositorioBase[Equipamento]):
    modelo = Equipamento

    async def listar(
        self, id_familia: UUID | None, busca: str | None, ativo: bool | None, limit: int, offset: int
    ) -> tuple[list[Equipamento], int]:
        filtros: list[ColumnElement[bool]] = []
        if id_familia:
            filtros.append(Equipamento.id_familia == id_familia)
        if busca:
            filtros.append(
                or_(
                    Equipamento.codigo_pedido.icontains(busca, autoescape=True),
                    Equipamento.nome.icontains(busca, autoescape=True),
                )
            )
        if ativo is not None:
            filtros.append(Equipamento.ativo.is_(ativo))
        return await self.paginar(filtros, [Equipamento.codigo_pedido], limit, offset)

    async def codigo_em_uso(self, id_familia: UUID, codigo_pedido: str, ignorar_id: UUID | None = None) -> bool:
        return await self.existe(
            Equipamento.id_familia == id_familia,
            func.upper(Equipamento.codigo_pedido) == codigo_pedido.upper(),
            *_diferente_de(Equipamento.id_equipamento, ignorar_id),
        )
