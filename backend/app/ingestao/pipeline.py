import asyncio
from uuid import UUID

import structlog
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.armazenamento.base import ArmazenamentoArquivos
from app.core.config import Settings
from app.core.errors import RegraNegocio, ServicoIndisponivel
from app.documentos.models import Documento, Idioma, StatusProcessamento
from app.ia.embedding import ProvedorEmbedding
from app.ingestao.chunking import TrechoCandidato, chunkar_paginas
from app.ingestao.extracao import extrair_paginas
from app.trechos.models import Trecho

log = structlog.get_logger()


async def processar_documento(
    session: AsyncSession,
    *,
    armazenamento: ArmazenamentoArquivos,
    embedding: ProvedorEmbedding,
    settings: Settings,
    id_documento: UUID,
) -> None:
    documento = await session.get(Documento, id_documento)
    if documento is None:
        log.warning("ingestao_documento_ausente", id_documento=str(id_documento))
        return
    if not documento.chave_arquivo:
        raise RegraNegocio("Documento sem arquivo para processar.")

    documento.status_processamento = StatusProcessamento.PROCESSANDO
    documento.erro_processamento = None
    await session.commit()

    try:
        pdf = await armazenamento.carregar(documento.chave_arquivo)
        paginas = await asyncio.to_thread(extrair_paginas, pdf)
        documento.paginas = len(paginas)

        candidatos = chunkar_paginas(paginas, tamanho_max_chars=settings.ingestao_tamanho_trecho_chars)
        if not candidatos:
            raise RegraNegocio("Nenhum texto extraível no PDF (documento escaneado ou vazio).")

        textos = [_texto_para_embedding(c, documento) for c in candidatos]
        vetores = await _embed_em_lotes(
            embedding,
            textos,
            max_chars_lote=settings.ingestao_max_chars_lote_embedding,
        )
        if len(vetores) != len(candidatos):
            raise ServicoIndisponivel(f"Embedding devolveu {len(vetores)} vetores para {len(candidatos)} trechos.")

        await session.execute(delete(Trecho).where(Trecho.id_documento == id_documento))
        for ordem, (candidato, vetor) in enumerate(zip(candidatos, vetores, strict=True)):
            session.add(
                Trecho(
                    id_documento=id_documento,
                    ordem=ordem,
                    conteudo=candidato.conteudo,
                    secao=candidato.secao,
                    pagina=candidato.pagina,
                    tipo_conteudo=candidato.tipo_conteudo,
                    embedding=vetor,
                )
            )
        await session.flush()
        await _atualizar_tsvector(session, id_documento, documento.idioma)

        documento.status_processamento = StatusProcessamento.INDEXADO
        documento.erro_processamento = None
        await session.commit()
        log.info(
            "ingestao_concluida",
            id_documento=str(id_documento),
            paginas=documento.paginas,
            trechos=len(candidatos),
        )
    except Exception as erro:
        await session.rollback()
        documento = await session.get(Documento, id_documento)
        if documento is not None:
            documento.status_processamento = StatusProcessamento.ERRO
            documento.erro_processamento = str(erro)[:2000]
            await session.commit()
        log.exception("ingestao_falhou", id_documento=str(id_documento))
        raise


async def processar_documento_em_background(
    sessionmaker: async_sessionmaker[AsyncSession],
    *,
    armazenamento: ArmazenamentoArquivos,
    embedding: ProvedorEmbedding,
    settings: Settings,
    id_documento: UUID,
) -> None:
    async with sessionmaker() as session:
        try:
            await processar_documento(
                session,
                armazenamento=armazenamento,
                embedding=embedding,
                settings=settings,
                id_documento=id_documento,
            )
        except Exception:
            # Erro já persistido em STATUS=ERRO; não propaga no BackgroundTasks
            return


def _texto_para_embedding(candidato: TrechoCandidato, documento: Documento) -> str:
    partes = [documento.titulo]
    if candidato.secao:
        partes.append(candidato.secao)
    if candidato.pagina is not None:
        partes.append(f"p.{candidato.pagina}")
    cabecalho = " | ".join(partes)
    return f"[{cabecalho}]\n{candidato.conteudo}"


async def _embed_em_lotes(
    embedding: ProvedorEmbedding,
    textos: list[str],
    *,
    max_chars_lote: int,
) -> list[list[float]]:
    if not textos:
        return []
    vetores: list[list[float]] = []
    inicio = 0
    while inicio < len(textos):
        lote: list[str] = []
        chars = 0
        while inicio < len(textos):
            tamanho = len(textos[inicio])
            if lote and chars + tamanho > max_chars_lote:
                break
            lote.append(textos[inicio])
            chars += tamanho
            inicio += 1
            if tamanho > max_chars_lote:
                break
        vetores.extend(await embedding.embed_documento(lote))
    return vetores


async def _atualizar_tsvector(session: AsyncSession, id_documento: UUID, idioma: Idioma) -> None:
    config = "portuguese" if idioma == Idioma.PT_BR else "english"
    await session.execute(
        text('UPDATE "TRECHOS" SET "CONTEUDO_BUSCA" = to_tsvector(:config, "CONTEUDO") WHERE "ID_DOCUMENTO" = :id'),
        {"config": config, "id": id_documento},
    )
