from typing import Any
from uuid import UUID

from sqlalchemy import ColumnElement, func, or_, select

from app.core.repository import RepositorioBase
from app.documentos.models import Idioma
from app.parametros.models import Parametro


def _diferente_de(coluna: Any, id_: UUID | None) -> list[ColumnElement[bool]]:
    return [coluna != id_] if id_ else []


class ParametroRepository(RepositorioBase[Parametro]):
    modelo = Parametro

    async def listar(
        self,
        *,
        id_familia: UUID | None,
        codigo: str | None,
        versao_firmware: str | None,
        idioma: Idioma | None,
        busca: str | None,
        ativo: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Parametro], int]:
        filtros: list[ColumnElement[bool]] = []
        if id_familia:
            filtros.append(Parametro.id_familia == id_familia)
        if codigo:
            filtros.append(func.lower(Parametro.codigo) == codigo.lower())
        if versao_firmware:
            filtros.append(or_(Parametro.versao_firmware == versao_firmware, Parametro.versao_firmware.is_(None)))
        if idioma:
            filtros.append(Parametro.idioma == idioma)
        if busca:
            filtros.append(
                or_(
                    Parametro.codigo.icontains(busca, autoescape=True),
                    Parametro.nome.icontains(busca, autoescape=True),
                    Parametro.descricao.icontains(busca, autoescape=True),
                )
            )
        if ativo is not None:
            filtros.append(Parametro.ativo.is_(ativo))
        return await self.paginar(filtros, [Parametro.codigo, Parametro.nome], limit, offset)

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
            Parametro.id_familia == id_familia,
            func.lower(Parametro.codigo) == codigo.lower(),
            Parametro.idioma == idioma,
            *_diferente_de(Parametro.id_parametro, ignorar_id),
        ]
        if versao_firmware is None:
            filtros.append(Parametro.versao_firmware.is_(None))
        else:
            filtros.append(Parametro.versao_firmware == versao_firmware)
        return await self.existe(*filtros)

    async def buscar_por_codigos(
        self,
        *,
        codigos: list[str],
        id_familia: UUID | None,
        versao_firmware: str | None,
        idioma: Idioma | None,
        limit: int = 20,
    ) -> list[Parametro]:
        if not codigos:
            return []
        codigos_lower = [c.lower() for c in codigos]
        filtros: list[ColumnElement[bool]] = [
            func.lower(Parametro.codigo).in_(codigos_lower),
            Parametro.ativo.is_(True),
        ]
        if id_familia:
            filtros.append(Parametro.id_familia == id_familia)
        if idioma:
            filtros.append(Parametro.idioma == idioma)
        if versao_firmware:
            filtros.append(or_(Parametro.versao_firmware == versao_firmware, Parametro.versao_firmware.is_(None)))
        consulta = (
            select(Parametro)
            .where(*filtros)
            .order_by(
                Parametro.versao_firmware.is_not(None).desc(),
                Parametro.codigo,
            )
            .limit(limit)
        )
        return list(await self.session.scalars(consulta))
