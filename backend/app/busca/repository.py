from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.documentos.models import Idioma, TipoDocumento


class BuscaRepository:
    """Busca híbrida: RRF entre ranking vetorial (cosseno) e textual (tsvector)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def buscar_hibrida(
        self,
        *,
        consulta: str,
        vetor: list[float],
        limit: int,
        candidatos: int,
        rrf_k: int,
        id_fabricante: UUID | None,
        id_familia: UUID | None,
        id_equipamento: UUID | None,
        tipo_documento: TipoDocumento | None,
        idioma: Idioma | None,
        versao_firmware: str | None,
    ) -> list[dict[str, Any]]:
        filtros_doc = [
            "d.\"STATUS_PROCESSAMENTO\" = 'INDEXADO'",
            't."EMBEDDING" IS NOT NULL',
            't."CONTEUDO_BUSCA" IS NOT NULL',
        ]
        params: dict[str, Any] = {
            "consulta": consulta,
            "vetor": str(vetor),
            "limit": limit,
            "candidatos": candidatos,
            "rrf_k": rrf_k,
        }

        if id_familia is not None:
            filtros_doc.append(
                'EXISTS (SELECT 1 FROM "DOCUMENTOS_FAMILIAS" df '
                'WHERE df."ID_DOCUMENTO" = d."ID_DOCUMENTO" AND df."ID_FAMILIA" = :id_familia)'
            )
            params["id_familia"] = id_familia
        if id_equipamento is not None:
            filtros_doc.append(
                'EXISTS (SELECT 1 FROM "DOCUMENTOS_EQUIPAMENTOS" de '
                'WHERE de."ID_DOCUMENTO" = d."ID_DOCUMENTO" AND de."ID_EQUIPAMENTO" = :id_equipamento)'
            )
            params["id_equipamento"] = id_equipamento
        if id_fabricante is not None:
            filtros_doc.append(
                'EXISTS (SELECT 1 FROM "DOCUMENTOS_FAMILIAS" df2 '
                'JOIN "FAMILIAS" f ON f."ID_FAMILIA" = df2."ID_FAMILIA" '
                'WHERE df2."ID_DOCUMENTO" = d."ID_DOCUMENTO" AND f."ID_FABRICANTE" = :id_fabricante)'
            )
            params["id_fabricante"] = id_fabricante
        if tipo_documento is not None:
            filtros_doc.append('d."TIPO_DOCUMENTO" = :tipo_documento')
            params["tipo_documento"] = tipo_documento.value
        if idioma is not None:
            filtros_doc.append('d."IDIOMA" = :idioma')
            params["idioma"] = idioma.value
        if versao_firmware is not None:
            filtros_doc.append('d."VERSAO_FIRMWARE" = :versao_firmware')
            params["versao_firmware"] = versao_firmware

        where_docs = " AND ".join(filtros_doc)
        # Fragmentos de WHERE são literais controlados + binds; sem interpolar input do usuário.
        sql = f"""
WITH base AS (
    SELECT
        t."ID_TRECHO" AS id_trecho,
        t."ID_DOCUMENTO" AS id_documento,
        t."CONTEUDO" AS conteudo,
        t."SECAO" AS secao,
        t."PAGINA" AS pagina,
        t."TIPO_CONTEUDO" AS tipo_conteudo,
        t."EMBEDDING" AS embedding,
        t."CONTEUDO_BUSCA" AS conteudo_busca,
        d."TITULO" AS titulo_documento,
        d."TIPO_DOCUMENTO" AS tipo_documento,
        d."IDIOMA" AS idioma,
        d."CODIGO_DOCUMENTO" AS codigo_documento,
        d."VERSAO_FIRMWARE" AS versao_firmware,
        CASE WHEN d."IDIOMA" = 'pt-BR' THEN 'portuguese' ELSE 'english' END AS config_texto
    FROM "TRECHOS" t
    JOIN "DOCUMENTOS" d ON d."ID_DOCUMENTO" = t."ID_DOCUMENTO"
    WHERE {where_docs}
),
semantica AS (
    SELECT
        id_trecho,
        (embedding <=> CAST(:vetor AS vector)) AS distancia_cosseno,
        ROW_NUMBER() OVER (ORDER BY embedding <=> CAST(:vetor AS vector)) AS rank_sem
    FROM base
    ORDER BY embedding <=> CAST(:vetor AS vector)
    LIMIT :candidatos
),
textual AS (
    SELECT
        id_trecho,
        ts_rank_cd(conteudo_busca, plainto_tsquery(config_texto::regconfig, :consulta)) AS rank_textual,
        ROW_NUMBER() OVER (
            ORDER BY ts_rank_cd(conteudo_busca, plainto_tsquery(config_texto::regconfig, :consulta)) DESC
        ) AS rank_txt
    FROM base
    WHERE conteudo_busca @@ plainto_tsquery(config_texto::regconfig, :consulta)
    ORDER BY ts_rank_cd(conteudo_busca, plainto_tsquery(config_texto::regconfig, :consulta)) DESC
    LIMIT :candidatos
),
fundido AS (
    SELECT
        COALESCE(s.id_trecho, t.id_trecho) AS id_trecho,
        COALESCE(1.0 / (:rrf_k + s.rank_sem), 0) + COALESCE(1.0 / (:rrf_k + t.rank_txt), 0) AS score,
        s.distancia_cosseno,
        t.rank_textual
    FROM semantica s
    FULL OUTER JOIN textual t ON t.id_trecho = s.id_trecho
)
SELECT
    b.id_trecho,
    b.id_documento,
    b.titulo_documento,
    b.tipo_documento,
    b.idioma,
    b.codigo_documento,
    b.versao_firmware,
    b.conteudo,
    b.secao,
    b.pagina,
    b.tipo_conteudo,
    f.score,
    f.distancia_cosseno,
    f.rank_textual
FROM fundido f
JOIN base b ON b.id_trecho = f.id_trecho
ORDER BY f.score DESC, f.distancia_cosseno ASC NULLS LAST
LIMIT :limit
"""  # noqa: S608
        resultado = await self.session.execute(text(sql), params)
        return [dict(row) for row in resultado.mappings().all()]
