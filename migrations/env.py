import asyncio
from logging.config import fileConfig
from typing import Literal

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql.schema import SchemaItem

from app.core.config import get_settings
from app.models import Base

type TipoObjeto = Literal[
    "schema", "table", "column", "index", "unique_constraint", "foreign_key_constraint", "check_constraint"
]

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def url_banco() -> str:
    return config.get_main_option("sqlalchemy.url") or str(get_settings().database_url)


def include_object(
    objeto: SchemaItem,
    nome: str | None,
    tipo: TipoObjeto,
    refletido: bool,
    comparado_com: SchemaItem | None,
) -> bool:
    return not (tipo == "table" and refletido and comparado_com is None)


def run_migrations_offline() -> None:
    context.configure(
        url=url_banco(),
        target_metadata=target_metadata,
        include_object=include_object,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(url_banco(), poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
