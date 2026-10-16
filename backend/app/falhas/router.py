from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.auth.deps import exigir_operacao_escrita, exigir_usuario
from app.core.schemas import Pagina, PaginacaoDep
from app.documentos.models import Idioma
from app.falhas.deps import FalhaServiceDep
from app.falhas.models import TipoFalha
from app.falhas.schemas import FalhaCreate, FalhaOut, FalhaUpdate

_auth = [Depends(exigir_usuario)]
_escrita = [Depends(exigir_operacao_escrita)]

router = APIRouter(prefix="/v1/falhas", tags=["falhas"], dependencies=_auth)


@router.get("")
async def listar_falhas(
    service: FalhaServiceDep,
    paginacao: PaginacaoDep,
    id_familia: Annotated[UUID | None, Query()] = None,
    codigo: Annotated[str | None, Query(max_length=40)] = None,
    tipo: Annotated[TipoFalha | None, Query()] = None,
    versao_firmware: Annotated[str | None, Query(max_length=30)] = None,
    idioma: Annotated[Idioma | None, Query()] = None,
    busca: Annotated[str | None, Query(max_length=100)] = None,
    ativo: Annotated[bool | None, Query()] = None,
) -> Pagina[FalhaOut]:
    return await service.listar(
        id_familia=id_familia,
        codigo=codigo,
        tipo=tipo,
        versao_firmware=versao_firmware,
        idioma=idioma,
        busca=busca,
        ativo=ativo,
        limit=paginacao.limit,
        offset=paginacao.offset,
    )


@router.get("/{id_falha}")
async def obter_falha(id_falha: UUID, service: FalhaServiceDep) -> FalhaOut:
    return await service.obter(id_falha)


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=_escrita)
async def criar_falha(dados: FalhaCreate, service: FalhaServiceDep) -> FalhaOut:
    return await service.criar(dados)


@router.patch("/{id_falha}", dependencies=_escrita)
async def alterar_falha(id_falha: UUID, dados: FalhaUpdate, service: FalhaServiceDep) -> FalhaOut:
    return await service.alterar(id_falha, dados)


@router.delete("/{id_falha}", status_code=status.HTTP_204_NO_CONTENT, dependencies=_escrita)
async def excluir_falha(id_falha: UUID, service: FalhaServiceDep) -> None:
    await service.excluir(id_falha)
