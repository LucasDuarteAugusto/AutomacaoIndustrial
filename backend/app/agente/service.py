from app.agente.prompts import (
    RESPOSTA_SEM_CONTEXTOS,
    SISTEMA_QA,
    formatar_trecho_contexto,
    montar_mensagem_usuario,
)
from app.agente.schemas import AgentePerguntaRequest, AgenteRespostaOut, CitacaoOut
from app.busca.schemas import BuscaRequest, TrechoBuscaOut
from app.busca.service import BuscaService
from app.core.errors import RegraNegocio
from app.ia.llm import ProvedorLLM


class AgenteService:
    def __init__(self, busca: BuscaService, llm: ProvedorLLM) -> None:
        self.busca = busca
        self.llm = llm

    async def perguntar(self, dados: AgentePerguntaRequest) -> AgenteRespostaOut:
        pergunta = dados.pergunta.strip()
        if not pergunta:
            raise RegraNegocio("Pergunta vazia.")

        resultado = await self.busca.buscar(
            BuscaRequest(
                consulta=pergunta,
                limit=dados.limit,
                id_fabricante=dados.id_fabricante,
                id_familia=dados.id_familia,
                id_equipamento=dados.id_equipamento,
                tipo_documento=dados.tipo_documento,
                idioma=dados.idioma,
                versao_firmware=dados.versao_firmware,
            )
        )

        if not resultado.items:
            return AgenteRespostaOut(
                pergunta=pergunta,
                resposta=RESPOSTA_SEM_CONTEXTOS,
                citacoes=[],
                modelo_llm=self.llm.modelo,
                trechos_consultados=0,
            )

        trechos_formatados = "\n\n".join(
            formatar_trecho_contexto(
                indice=i,
                titulo_documento=item.titulo_documento,
                secao=item.secao,
                pagina=item.pagina,
                conteudo=item.conteudo,
            )
            for i, item in enumerate(resultado.items, start=1)
        )
        resposta = await self.llm.completar(
            sistema=SISTEMA_QA,
            usuario=montar_mensagem_usuario(pergunta=pergunta, trechos_formatados=trechos_formatados),
        )
        return AgenteRespostaOut(
            pergunta=pergunta,
            resposta=resposta.strip(),
            citacoes=[_citacao(i, item) for i, item in enumerate(resultado.items, start=1)],
            modelo_llm=self.llm.modelo,
            trechos_consultados=len(resultado.items),
        )


def _citacao(indice: int, item: TrechoBuscaOut) -> CitacaoOut:
    return CitacaoOut(
        indice=indice,
        id_trecho=item.id_trecho,
        id_documento=item.id_documento,
        titulo_documento=item.titulo_documento,
        codigo_documento=item.codigo_documento,
        secao=item.secao,
        pagina=item.pagina,
        trecho=item.conteudo,
        score=item.score,
    )
