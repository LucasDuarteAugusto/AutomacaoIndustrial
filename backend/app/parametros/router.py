from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.auth.deps import exigir_operacao_escrita, exigir_usuario
from app.core.schemas import Pagina, PaginacaoDep
from app.documentos.models import Idioma
from app.parametros.deps import ParametroServiceDep
from app.parametros.schemas import ParametroCreate, ParametroOut, ParametroUpdate

_auth = [Depends(exigir_usuario)]
_escrita = [Depends(exigir_operacao_escrita)]

router = APIRouter(prefix="/v1/parametros", tags=["parametros"], dependencies=_auth)


@router.get("")
async def listar_parametros(
    service: ParametroServiceDep,
    paginacao: PaginacaoDep,
    id_familia: Annotated[UUID | None, Query()] = None,
    codigo: Annotated[str | None, Query(max_length=40)] = None,
    versao_firmware: Annotated[str | None, Query(max_length=30)] = None,
    idioma: Annotated[Idioma | None, Query()] = None,
    busca: Annotated[str | None, Query(max_length=100)] = None,
    ativo: Annotated[bool | None, Query()] = None,
) -> Pagina[ParametroOut]:
    return await service.listar(
        id_familia=id_familia,
        codigo=codigo,
        versao_firmware=versao_firmware,
        idioma=idioma,
        busca=busca,
        ativo=ativo,
        limit=paginacao.limit,
        offset=paginacao.offset,
    )


@router.get("/{id_parametro}")
async def obter_parametro(id_parametro: UUID, service: ParametroServiceDep) -> ParametroOut:
    return await service.obter(id_parametro)


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=_escrita)
async def criar_parametro(dados: ParametroCreate, service: ParametroServiceDep) -> ParametroOut:
    return await service.criar(dados)


@router.patch("/{id_parametro}", dependencies=_escrita)
async def alterar_parametro(id_parametro: UUID, dados: ParametroUpdate, service: ParametroServiceDep) -> ParametroOut:
    return await service.alterar(id_parametro, dados)


@router.delete("/{id_parametro}", status_code=status.HTTP_204_NO_CONTENT, dependencies=_escrita)
async def excluir_parametro(id_parametro: UUID, service: ParametroServiceDep) -> None:
    await service.excluir(id_parametro)
