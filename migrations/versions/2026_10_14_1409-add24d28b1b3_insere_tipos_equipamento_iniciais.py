"""insere_tipos_equipamento_iniciais

Create Date: 2026-10-14 14:09:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert

revision: str = "add24d28b1b3"
down_revision: str | Sequence[str] | None = "b1d21174385c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

tipos_equipamento = sa.table(
    "TIPOS_EQUIPAMENTO",
    sa.column("CODIGO", sa.String),
    sa.column("NOME", sa.String),
    sa.column("DESCRICAO", sa.Text),
)

TIPOS_INICIAIS = [
    {
        "CODIGO": "RELE_GERENCIAMENTO",
        "NOME": "Relé de gerenciamento de motor",
        "DESCRICAO": "Proteção, monitoramento e lógica de partida do motor via rede (ex.: Siemens SIMOCODE pro).",
    },
    {
        "CODIGO": "SOFT_STARTER",
        "NOME": "Soft starter",
        "DESCRICAO": "Partida e parada suaves por controle de tensão, limitando corrente e golpe mecânico.",
    },
    {
        "CODIGO": "INVERSOR",
        "NOME": "Inversor de frequência",
        "DESCRICAO": "Controle de velocidade e torque do motor por variação de frequência e tensão.",
    },
]


def upgrade() -> None:
    op.execute(insert(tipos_equipamento).values(TIPOS_INICIAIS).on_conflict_do_nothing(index_elements=["CODIGO"]))


def downgrade() -> None:
    codigos = [t["CODIGO"] for t in TIPOS_INICIAIS]
    op.execute(tipos_equipamento.delete().where(tipos_equipamento.c.CODIGO.in_(codigos)))
