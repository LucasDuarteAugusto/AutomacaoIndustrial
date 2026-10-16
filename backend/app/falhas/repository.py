from typing import Any
from uuid import UUID

from sqlalchemy import ColumnElement, func, or_, select

from app.core.repository import RepositorioBase
from app.documentos.models import Idioma
from app.falhas.models import Falha, TipoFalha


def _diferente_de(coluna: Any, id_: UUID | None) -> list[ColumnElement[bool]]:
    return [coluna != id_] if id_ else []


class FalhaRepository(RepositorioBase[Falha]):
    modelo = Falha

    async def listar(
        self,
        *,
        id_familia: UUID | None,
        codigo: str | None,
        tipo: TipoFalha | None,
        versao_firmware: str | None,
        idioma: Idioma | None,
        busca: str | None,
        ativo: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Falha], int]:
        filtros: list[ColumnElement[bool]] = []
        if id_familia:
            filtros.append(Falha.id_familia == id_familia)
        if codigo:
            filtros.append(func.lower(Falha.codigo) == codigo.lower())
        if tipo:
            filtros.append(Falha.tipo == tipo)
        if versao_firmware:
            filtros.append(or_(Falha.versao_firmware == versao_firmware, Falha.versao_firmware.is_(None)))
        if idioma:
            filtros.append(Falha.idioma == idioma)
        if busca:
            filtros.append(
                or_(
                    Falha.codigo.icontains(busca, autoescape=True),
                    Falha.titulo.icontains(busca, autoescape=True),
                    Falha.descricao.icontains(busca, autoescape=True),
                    Falha.causa.icontains(busca, autoescape=True),
                    Falha.solucao.icontains(busca, autoescape=True),
                )
            )
        if ativo is not None:
            filtros.append(Falha.ativo.is_(ativo))
        return await self.paginar(filtros, [Falha.codigo, Falha.titulo], limit, offset)

    async def codigo_em_uso(
        self,
        *,
        id_familia: UUID,
        codigo: str,
        idioma: Idioma,
        versao_firmware: str | None,
        ignorar_id: UUID | None = None,
    ) -> bool:
        filtros = [
            Falha.id_familia == id_familia,
            func.lower(Falha.codigo) == codigo.lower(),
            Falha.idioma == idioma,
            *_diferente_de(Falha.id_falha, ignorar_id),
        ]
        if versao_firmware is None:
            filtros.append(Falha.versao_firmware.is_(None))
        else:
            filtros.append(Falha.versao_firmware == versao_firmware)
        return await self.existe(*filtros)

    async def buscar_por_codigos(
        self,
        *,
        codigos: list[str],
        id_familia: UUID | None,
        versao_firmware: str | None,
        idioma: Idioma | None,
        limit: int = 20,
    ) -> list[Falha]:
        if not codigos:
            return []
        codigos_lower = [c.lower() for c in codigos]
        filtros: list[ColumnElement[bool]] = [
            func.lower(Falha.codigo).in_(codigos_lower),
            Falha.ativo.is_(True),
        ]
        if id_familia:
            filtros.append(Falha.id_familia == id_familia)
        if idioma:
            filtros.append(Falha.idioma == idioma)
        if versao_firmware:
            filtros.append(or_(Falha.versao_firmware == versao_firmware, Falha.versao_firmware.is_(None)))
        consulta = (
            select(Falha).where(*filtros).order_by(Falha.versao_firmware.is_not(None).desc(), Falha.codigo).limit(limit)
        )
        return list(await self.session.scalars(consulta))
