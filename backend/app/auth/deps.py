from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.models import Perfil, Usuario
from app.auth.seguranca import decodificar_access_token
from app.auth.service import AuthService, exigir_escrita
from app.core.deps import SessionDep, SettingsDep
from app.core.errors import NaoAutorizado, Proibido

_bearer = HTTPBearer(auto_error=False)


def get_auth_service(session: SessionDep, settings: SettingsDep) -> AuthService:
    return AuthService(session, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_usuario_atual(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    settings: SettingsDep,
    service: AuthServiceDep,
) -> Usuario:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise NaoAutorizado("Informe o header Authorization: Bearer <token>.")
    payload = decodificar_access_token(credentials.credentials, settings)
    try:
        id_usuario = UUID(str(payload["sub"]))
    except (KeyError, ValueError, TypeError) as erro:
        raise NaoAutorizado("Token com sujeito inválido.") from erro
    return await service.obter_usuario(id_usuario)


UsuarioAtualDep = Annotated[Usuario, Depends(get_usuario_atual)]


async def exigir_usuario(usuario: UsuarioAtualDep) -> Usuario:
    return usuario


async def exigir_admin(usuario: UsuarioAtualDep) -> Usuario:
    if usuario.perfil != Perfil.ADMIN:
        raise Proibido("Apenas ADMIN.")
    return usuario


async def exigir_operacao_escrita(usuario: UsuarioAtualDep) -> Usuario:
    exigir_escrita(usuario)
    return usuario


def usuario_para_teste(perfil: Perfil = Perfil.ADMIN) -> Usuario:
    """Usuário sintético para dependency_overrides nos testes."""
    return Usuario(
        email="teste@example.com",
        senha_hash="x",
        nome="Teste",
        perfil=perfil,
        ativo=True,
    )
