from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.auth.models import Perfil
from app.core.config import Settings
from app.core.errors import NaoAutorizado

_password_hash = PasswordHash.recommended()


def hash_senha(senha: str) -> str:
    return _password_hash.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return _password_hash.verify(senha, senha_hash)


def criar_access_token(
    *,
    settings: Settings,
    id_usuario: UUID,
    email: str,
    perfil: Perfil,
) -> str:
    agora = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(id_usuario),
        "email": email,
        "perfil": perfil.value,
        "iat": agora,
        "exp": agora + timedelta(minutes=settings.jwt_expiracao_minutos),
    }
    return jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm)


def decodificar_access_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as erro:
        raise NaoAutorizado("Token inválido ou expirado.") from erro
    if not isinstance(payload, dict) or "sub" not in payload:
        raise NaoAutorizado("Token sem sujeito (sub).")
    return payload
