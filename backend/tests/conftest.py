from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from testcontainers.community.postgres import PostgresContainer

from app.core.config import Settings
from app.core.db import get_session
from app.main import create_app

IMAGEM_POSTGRES = "pgvector/pgvector:pg17"
RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    with PostgresContainer(IMAGEM_POSTGRES, driver="asyncpg") as postgres:
        url: str = postgres.get_connection_url()
        alembic_cfg = Config(toml_file=str(RAIZ / "pyproject.toml"))
        alembic_cfg.set_main_option("sqlalchemy.url", url)
        command.upgrade(alembic_cfg, "head")
        yield url


@pytest.fixture(scope="session")
def settings(database_url: str, tmp_path_factory: pytest.TempPathFactory) -> Settings:
    pasta_arquivos = tmp_path_factory.mktemp("arquivos")
    return Settings(
        database_url=database_url,
        ambiente="teste",
        armazenamento_tipo="local",
        armazenamento_caminho=str(pasta_arquivos),
    )


@pytest.fixture(scope="session")
async def app(settings: Settings) -> AsyncIterator[FastAPI]:
    aplicacao = create_app(settings)
    async with aplicacao.router.lifespan_context(aplicacao):
        yield aplicacao


@pytest.fixture
async def db_session(app: FastAPI) -> AsyncIterator[AsyncSession]:
    engine: AsyncEngine = app.state.engine
    async with engine.connect() as conexao:
        transacao = await conexao.begin()
        session = AsyncSession(bind=conexao, expire_on_commit=False, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            await session.close()
            await transacao.rollback()


@pytest.fixture
async def client(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def _session_de_teste() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session_de_teste
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente:
        yield cliente
    app.dependency_overrides.clear()
