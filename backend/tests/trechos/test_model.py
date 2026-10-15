from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ia_defaults import EMBEDDING_DIMENSAO_PADRAO
from app.documentos.models import Documento, Idioma, TipoDocumento
from app.trechos.models import TipoConteudo, Trecho


async def _documento(db_session: AsyncSession) -> Documento:
    documento = Documento(
        titulo="Lista de parâmetros — teste",
        tipo_documento=TipoDocumento.LISTA_PARAMETROS,
        idioma=Idioma.PT_BR,
    )
    db_session.add(documento)
    await db_session.flush()
    return documento


async def test_persiste_trecho_com_embedding_e_tsvector(db_session: AsyncSession) -> None:
    documento = await _documento(db_session)
    vetor = [0.0] * EMBEDDING_DIMENSAO_PADRAO
    vetor[0] = 1.0

    trecho = Trecho(
        id_documento=documento.id_documento,
        ordem=0,
        conteudo="Tempo de rampa de aceleração: 10 s (padrão).",
        secao="3.2 Parâmetros de partida",
        pagina=42,
        tipo_conteudo=TipoConteudo.TEXTO,
        embedding=vetor,
    )
    db_session.add(trecho)
    await db_session.flush()

    await db_session.execute(
        text('UPDATE "TRECHOS" SET "CONTEUDO_BUSCA" = to_tsvector(\'portuguese\', "CONTEUDO") WHERE "ID_TRECHO" = :id'),
        {"id": trecho.id_trecho},
    )
    await db_session.flush()

    carregado = await db_session.scalar(select(Trecho).where(Trecho.id_trecho == trecho.id_trecho))
    assert carregado is not None
    assert carregado.embedding is not None
    assert len(carregado.embedding) == EMBEDDING_DIMENSAO_PADRAO
    assert carregado.conteudo_busca is not None

    distancia = await db_session.scalar(
        text('SELECT "EMBEDDING" <=> CAST(:vetor AS vector) FROM "TRECHOS" WHERE "ID_TRECHO" = :id'),
        {"vetor": str(vetor), "id": trecho.id_trecho},
    )
    assert distancia == 0.0


async def test_indices_hnsw_e_gin_existem(db_session: AsyncSession) -> None:
    nomes = (
        await db_session.scalars(
            text(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'TRECHOS'
                  AND indexname IN ('IDX_TRECHOS_EMBEDDING_HNSW', 'IDX_TRECHOS_CONTEUDO_BUSCA')
                ORDER BY indexname
                """
            )
        )
    ).all()
    assert nomes == ["IDX_TRECHOS_CONTEUDO_BUSCA", "IDX_TRECHOS_EMBEDDING_HNSW"]
