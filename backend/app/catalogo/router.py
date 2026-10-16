from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.auth.deps import exigir_operacao_escrita, exigir_usuario
from app.catalogo.deps import (
    EquipamentoServiceDep,
    FabricanteServiceDep,
    FamiliaServiceDep,
    TipoEquipamentoServiceDep,
)
from app.catalogo.schemas import (
    EquipamentoCreate,
    EquipamentoOut,
    EquipamentoUpdate,
    FabricanteCreate,
    FabricanteOut,
    FabricanteUpdate,
    FamiliaCreate,
    FamiliaOut,
    FamiliaUpdate,
    TipoEquipamentoOut,
)
from app.core.schemas import Pagina, PaginacaoDep

Busca = Annotated[str | None, Query(max_length=100, description="Texto contido no nome")]
Ativo = Annotated[bool | None, Query(description="Filtra por ativo/inativo")]
_auth = [Depends(exigir_usuario)]
_escrita = [Depends(exigir_operacao_escrita)]

tipos_router = APIRouter(prefix="/v1/tipos-equipamento", tags=["tipos-equipamento"], dependencies=_auth)
fabricantes_router = APIRouter(prefix="/v1/fabricantes", tags=["fabricantes"], dependencies=_auth)
familias_router = APIRouter(prefix="/v1/familias", tags=["familias"], dependencies=_auth)
equipamentos_router = APIRouter(prefix="/v1/equipamentos", tags=["equipamentos"], dependencies=_auth)


@tipos_router.get("")
async def listar_tipos(service: TipoEquipamentoServiceDep, pagina: PaginacaoDep) -> Pagina[TipoEquipamentoOut]:
    return await service.listar(pagina.limit, pagina.offset)


@tipos_router.get("/{id_tipo_equipamento}")
async def obter_tipo(id_tipo_equipamento: UUID, service: TipoEquipamentoServiceDep) -> TipoEquipamentoOut:
    return await service.obter(id_tipo_equipamento)


@fabricantes_router.get("")
async def listar_fabricantes(
    service: FabricanteServiceDep, pagina: PaginacaoDep, busca: Busca = None, ativo: Ativo = None
) -> Pagina[FabricanteOut]:
    return await service.listar(busca, ativo, pagina.limit, pagina.offset)


@fabricantes_router.get("/{id_fabricante}")
async def obter_fabricante(id_fabricante: UUID, service: FabricanteServiceDep) -> FabricanteOut:
    return await service.obter(id_fabricante)


@fabricantes_router.post("", status_code=status.HTTP_201_CREATED, dependencies=_escrita)
async def criar_fabricante(dados: FabricanteCreate, service: FabricanteServiceDep) -> FabricanteOut:
    return await service.criar(dados)


@fabricantes_router.patch("/{id_fabricante}", dependencies=_escrita)
async def alterar_fabricante(
    id_fabricante: UUID, dados: FabricanteUpdate, service: FabricanteServiceDep
) -> FabricanteOut:
    return await service.alterar(id_fabricante, dados)


@fabricantes_router.delete("/{id_fabricante}", status_code=status.HTTP_204_NO_CONTENT, dependencies=_escrita)
async def excluir_fabricante(id_fabricante: UUID, service: FabricanteServiceDep) -> None:
    await service.excluir(id_fabricante)


@familias_router.get("")
async def listar_familias(
    service: FamiliaServiceDep,
    pagina: PaginacaoDep,
    id_fabricante: UUID | None = None,
    id_tipo_equipamento: UUID | None = None,
    busca: Busca = None,
    ativo: Ativo = None,
) -> Pagina[FamiliaOut]:
    return await service.listar(id_fabricante, id_tipo_equipamento, busca, ativo, pagina.limit, pagina.offset)


@familias_router.get("/{id_familia}")
async def obter_familia(id_familia: UUID, service: FamiliaServiceDep) -> FamiliaOut:
    return await service.obter(id_familia)


@familias_router.post("", status_code=status.HTTP_201_CREATED, dependencies=_escrita)
async def criar_familia(dados: FamiliaCreate, service: FamiliaServiceDep) -> FamiliaOut:
    return await service.criar(dados)


@familias_router.patch("/{id_familia}", dependencies=_escrita)
async def alterar_familia(id_familia: UUID, dados: FamiliaUpdate, service: FamiliaServiceDep) -> FamiliaOut:
    return await service.alterar(id_familia, dados)


@familias_router.delete("/{id_familia}", status_code=status.HTTP_204_NO_CONTENT, dependencies=_escrita)
async def excluir_familia(id_familia: UUID, service: FamiliaServiceDep) -> None:
    await service.excluir(id_familia)


@equipamentos_router.get("")
async def listar_equipamentos(
    service: EquipamentoServiceDep,
    pagina: PaginacaoDep,
    id_familia: UUID | None = None,
    busca: Annotated[str | None, Query(max_length=100, description="Texto contido no código ou nome")] = None,
    ativo: Ativo = None,
) -> Pagina[EquipamentoOut]:
    return await service.listar(id_familia, busca, ativo, pagina.limit, pagina.offset)


@equipamentos_router.get("/{id_equipamento}")
async def obter_equipamento(id_equipamento: UUID, service: EquipamentoServiceDep) -> EquipamentoOut:
    return await service.obter(id_equipamento)


@equipamentos_router.post("", status_code=status.HTTP_201_CREATED, dependencies=_escrita)
async def criar_equipamento(dados: EquipamentoCreate, service: EquipamentoServiceDep) -> EquipamentoOut:
    return await service.criar(dados)


@equipamentos_router.patch("/{id_equipamento}", dependencies=_escrita)
async def alterar_equipamento(
    id_equipamento: UUID, dados: EquipamentoUpdate, service: EquipamentoServiceDep
) -> EquipamentoOut:
    return await service.alterar(id_equipamento, dados)


@equipamentos_router.delete("/{id_equipamento}", status_code=status.HTTP_204_NO_CONTENT, dependencies=_escrita)
async def excluir_equipamento(id_equipamento: UUID, service: EquipamentoServiceDep) -> None:
    await service.excluir(id_equipamento)


routers = [tipos_router, fabricantes_router, familias_router, equipamentos_router]
