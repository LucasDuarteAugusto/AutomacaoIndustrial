from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.auth.deps import AuthServiceDep, UsuarioAtualDep, exigir_admin
from app.auth.models import Perfil, Usuario
from app.auth.schemas import BootstrapRequest, LoginRequest, TokenOut, UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.core.schemas import Pagina, PaginacaoDep

router = APIRouter(prefix="/v1/auth", tags=["auth"])

AdminDep = Annotated[Usuario, Depends(exigir_admin)]


@router.post("/login", response_model=TokenOut)
async def login(dados: LoginRequest, service: AuthServiceDep) -> TokenOut:
    return await service.login(dados)


@router.post("/bootstrap", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
async def bootstrap(dados: BootstrapRequest, service: AuthServiceDep) -> TokenOut:
    """Cria o primeiro ADMIN quando a base ainda não tem usuários."""
    return await service.bootstrap(dados)


@router.get("/me", response_model=UsuarioOut)
async def me(usuario: UsuarioAtualDep) -> Usuario:
    return usuario


@router.get("/usuarios", dependencies=[Depends(exigir_admin)])
async def listar_usuarios(
    service: AuthServiceDep,
    pagina: PaginacaoDep,
    busca: Annotated[str | None, Query(max_length=100, description="Texto contido no nome ou e-mail")] = None,
    perfil: Perfil | None = None,
    ativo: Annotated[bool | None, Query(description="Filtra por ativo/inativo")] = None,
) -> Pagina[UsuarioOut]:
    return await service.listar_usuarios(busca, perfil, ativo, pagina.limit, pagina.offset)


@router.get("/usuarios/{id_usuario}", dependencies=[Depends(exigir_admin)])
async def obter_usuario(id_usuario: UUID, service: AuthServiceDep) -> UsuarioOut:
    return await service.obter_usuario_admin(id_usuario)


@router.post("/usuarios", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
async def criar_usuario(dados: UsuarioCreate, service: AuthServiceDep, ator: AdminDep) -> UsuarioOut:
    return await service.criar_usuario(dados, ator)


@router.patch("/usuarios/{id_usuario}", response_model=UsuarioOut)
async def alterar_usuario(
    id_usuario: UUID,
    dados: UsuarioUpdate,
    service: AuthServiceDep,
    ator: AdminDep,
) -> UsuarioOut:
    return await service.alterar_usuario(id_usuario, dados, ator)
