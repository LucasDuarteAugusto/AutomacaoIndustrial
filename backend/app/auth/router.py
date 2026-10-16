from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.auth.deps import AuthServiceDep, UsuarioAtualDep, exigir_admin
from app.auth.models import Usuario
from app.auth.schemas import BootstrapRequest, LoginRequest, TokenOut, UsuarioCreate, UsuarioOut, UsuarioUpdate

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
