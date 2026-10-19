from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import EmailStr, Field

from app.auth.models import Perfil
from app.core.schemas import Entrada, NaoNulo, Saida


class LoginRequest(Entrada):
    email: EmailStr
    senha: str = Field(min_length=6, max_length=128)


class BootstrapRequest(Entrada):
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    nome: str = Field(min_length=1, max_length=150)


class BootstrapStatusOut(Saida):
    necessario: bool = Field(description="True enquanto não houver nenhum usuário cadastrado")


class TrocaSenhaRequest(Entrada):
    senha_atual: str = Field(min_length=1, max_length=128)
    senha_nova: str = Field(min_length=8, max_length=128)


class UsuarioCreate(Entrada):
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    nome: str = Field(min_length=1, max_length=150)
    perfil: Perfil = Perfil.OPERADOR
    ativo: bool = True


class UsuarioUpdate(Entrada):
    nome: Annotated[str | None, NaoNulo] = Field(default=None, min_length=1, max_length=150)
    senha: Annotated[str | None, NaoNulo] = Field(default=None, min_length=8, max_length=128)
    perfil: Annotated[Perfil | None, NaoNulo] = None
    ativo: Annotated[bool | None, NaoNulo] = None


class UsuarioOut(Saida):
    id_usuario: UUID
    email: str
    nome: str
    perfil: Perfil
    ativo: bool
    created_at: datetime
    updated_at: datetime


class TokenOut(Saida):
    access_token: str
    token_type: str = "bearer"  # noqa: S105

    expires_in: int
    usuario: UsuarioOut
