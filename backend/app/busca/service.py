from sqlalchemy.ext.asyncio import AsyncSession

from app.busca.repository import BuscaRepository
from app.busca.schemas import BuscaOut, BuscaRequest, TrechoBuscaOut
from app.core.config import Settings
from app.core.errors import RegraNegocio
from app.documentos.models import Idioma, TipoDocumento
from app.ia.embedding import ProvedorEmbedding
from app.trechos.models import TipoConteudo


class BuscaService:
    def __init__(self, session: AsyncSession, embedding: ProvedorEmbedding, settings: Settings) -> None:
        self.session = session
        self.embedding = embedding
        self.settings = settings
        self.buscas = BuscaRepository(session)

    async def buscar(self, dados: BuscaRequest) -> BuscaOut:
        consulta = dados.consulta.strip()
        if not consulta:
            raise RegraNegocio("Consulta vazia.")

        vetor = await self.embedding.embed_consulta(consulta)
        if len(vetor) != self.settings.embedding_dimensao:
            raise RegraNegocio(
                f"Dimensão do embedding da consulta ({len(vetor)}) difere de {self.settings.embedding_dimensao}."
            )

        linhas = await self.buscas.buscar_hibrida(
            consulta=consulta,
            vetor=vetor,
            limit=dados.limit,
            candidatos=self.settings.busca_candidatos_por_modo,
            rrf_k=self.settings.busca_rrf_k,
            id_fabricante=dados.id_fabricante,
            id_familia=dados.id_familia,
            id_equipamento=dados.id_equipamento,
            tipo_documento=dados.tipo_documento,
            idioma=dados.idioma,
            versao_firmware=dados.versao_firmware,
        )

        items = [
            TrechoBuscaOut(
                id_trecho=linha["id_trecho"],
                id_documento=linha["id_documento"],
                titulo_documento=linha["titulo_documento"],
                tipo_documento=TipoDocumento(linha["tipo_documento"]),
                idioma=Idioma(linha["idioma"]),
                codigo_documento=linha["codigo_documento"],
                versao_firmware=linha["versao_firmware"],
                conteudo=linha["conteudo"],
                secao=linha["secao"],
                pagina=linha["pagina"],
                tipo_conteudo=TipoConteudo(linha["tipo_conteudo"]),
                score=float(linha["score"]),
                distancia_cosseno=float(linha["distancia_cosseno"]) if linha["distancia_cosseno"] is not None else None,
                rank_textual=float(linha["rank_textual"]) if linha["rank_textual"] is not None else None,
            )
            for linha in linhas
        ]
        return BuscaOut(consulta=consulta, items=items, total=len(items))
