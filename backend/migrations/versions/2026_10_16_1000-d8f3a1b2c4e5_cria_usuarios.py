"""cria_usuarios

Create Date: 2026-10-16 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d8f3a1b2c4e5"
down_revision: str | Sequence[str] | None = "c4e8f1a92b07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID_PADRAO = sa.text("gen_random_uuid()")
PERFIS = ("ADMIN", "OPERADOR", "LEITURA")


def _nao_existe(tabela: str) -> bool:
    return not sa.inspect(op.get_bind()).has_table(tabela)


def upgrade() -> None:
    if _nao_existe("USUARIOS"):
        op.create_table(
            "USUARIOS",
            sa.Column(
                "ID_USUARIO",
                sa.Uuid(),
                server_default=UUID_PADRAO,
                nullable=False,
                comment="Identificador do usuário",
            ),
            sa.Column("EMAIL", sa.String(255), nullable=False, comment="E-mail de login (único)"),
            sa.Column("SENHA_HASH", sa.String(255), nullable=False, comment="Hash Argon2 da senha"),
            sa.Column("NOME", sa.String(150), nullable=False, comment="Nome de exibição"),
            sa.Column(
                "PERFIL",
                sa.String(20),
                nullable=False,
                comment="Perfil de acesso (ADMIN, OPERADOR, LEITURA)",
            ),
            sa.Column(
                "ATIVO",
                sa.Boolean(),
                server_default=sa.true(),
                nullable=False,
                comment="Usuário pode autenticar",
            ),
            sa.Column(
                "createdAt",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
                comment="Data de criação do registro",
            ),
            sa.Column(
                "updatedAt",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
                comment="Data da última alteração do registro",
            ),
            sa.PrimaryKeyConstraint("ID_USUARIO", name="PK_USUARIOS"),
            sa.UniqueConstraint("EMAIL", name="UK_USUARIOS_EMAIL"),
            sa.CheckConstraint(
                '"PERFIL" IN (' + ", ".join(f"'{p}'" for p in PERFIS) + ")",
                name="CK_USUARIOS_PERFIL_USUARIO",
            ),
            comment="Usuários da API (autenticação JWT)",
        )


def downgrade() -> None:
    if not _nao_existe("USUARIOS"):
        op.drop_table("USUARIOS")
