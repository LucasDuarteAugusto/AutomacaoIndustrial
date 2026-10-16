from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import UUID_PADRAO, Base, TimestampMixin


class Perfil(StrEnum):
    ADMIN = "ADMIN"
    OPERADOR = "OPERADOR"
    LEITURA = "LEITURA"


def _enum_varchar(enum: type[StrEnum], nome: str, tamanho: int) -> Enum:
    return Enum(
        enum,
        name=nome,
        native_enum=False,
        create_constraint=True,
        length=tamanho,
        values_callable=lambda membros: [m.value for m in membros],
    )


class Usuario(TimestampMixin, Base):
    __tablename__ = "USUARIOS"
    __table_args__ = ({"comment": "Usuários da API (autenticação JWT)"},)

    id_usuario: Mapped[UUID] = mapped_column(
        "ID_USUARIO", primary_key=True, server_default=UUID_PADRAO, comment="Identificador do usuário"
    )
    email: Mapped[str] = mapped_column("EMAIL", String(255), unique=True, comment="E-mail de login (único)")
    senha_hash: Mapped[str] = mapped_column("SENHA_HASH", String(255), comment="Hash Argon2 da senha")
    nome: Mapped[str] = mapped_column("NOME", String(150), comment="Nome de exibição")
    perfil: Mapped[Perfil] = mapped_column(
        "PERFIL",
        _enum_varchar(Perfil, "PERFIL_USUARIO", 20),
        comment="Perfil de acesso (ADMIN, OPERADOR, LEITURA)",
    )
    ativo: Mapped[bool] = mapped_column("ATIVO", server_default=true(), comment="Usuário pode autenticar")
