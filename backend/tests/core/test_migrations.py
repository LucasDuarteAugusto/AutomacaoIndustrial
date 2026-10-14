from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def test_extensao_vector_habilitada_apos_migrations(db_session: AsyncSession) -> None:
    versao = await db_session.scalar(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'"))
    assert versao is not None


async def test_distancia_de_cosseno_funciona_no_banco(db_session: AsyncSession) -> None:
    distancia = await db_session.scalar(text("SELECT '[1,0,0]'::vector <=> '[0,1,0]'::vector"))
    assert distancia == 1.0
