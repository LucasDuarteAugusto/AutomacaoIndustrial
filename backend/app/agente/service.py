from app.agente.codigos import extrair_codigos_falha, extrair_codigos_parametro
from app.agente.prompts import (
    RESPOSTA_SEM_CONTEXTOS,
    SISTEMA_QA,
    formatar_falha_contexto,
    formatar_parametro_contexto,
    formatar_trecho_contexto,
    montar_mensagem_usuario,
)
from app.agente.schemas import AgentePerguntaRequest, AgenteRespostaOut, CitacaoOut
from app.busca.schemas import BuscaRequest, TrechoBuscaOut
from app.busca.service import BuscaService
from app.core.errors import RegraNegocio
from app.falhas.service import FalhaService
from app.ia.llm import ProvedorLLM
from app.parametros.service import ParametroService


class AgenteService:
    def __init__(
        self,
        busca: BuscaService,
        llm: ProvedorLLM,
        parametros: ParametroService,
        falhas: FalhaService,
    ) -> None:
        self.busca = busca
        self.llm = llm
        self.parametros = parametros
        self.falhas = falhas

    async def perguntar(self, dados: AgentePerguntaRequest) -> AgenteRespostaOut:
        pergunta = dados.pergunta.strip()
        if not pergunta:
            raise RegraNegocio("Pergunta vazia.")

        hits_parametros = await self.parametros.buscar_por_codigos(
            codigos=extrair_codigos_parametro(pergunta),
            id_familia=dados.id_familia,
            versao_firmware=dados.versao_firmware,
            idioma=dados.idioma,
        )
        hits_falhas = await self.falhas.buscar_por_codigos(
            codigos=extrair_codigos_falha(pergunta),
            id_familia=dados.id_familia,
            versao_firmware=dados.versao_firmware,
            idioma=dados.idioma,
        )

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

        if not resultado.items and not hits_parametros and not hits_falhas:
            return AgenteRespostaOut(
                pergunta=pergunta,
                resposta=RESPOSTA_SEM_CONTEXTOS,
                citacoes=[],
                parametros=[],
                falhas=[],
                modelo_llm=self.llm.modelo,
                trechos_consultados=0,
            )

        blocos_estruturados: list[str] = []
        for i, parametro in enumerate(hits_parametros, start=1):
            blocos_estruturados.append(
                formatar_parametro_contexto(
                    indice=i,
                    codigo=parametro.codigo,
                    nome=parametro.nome,
                    descricao=parametro.descricao,
                    unidade=parametro.unidade,
                    valor_min=parametro.valor_min,
                    valor_max=parametro.valor_max,
                    valor_padrao=parametro.valor_padrao,
                    grupo=parametro.grupo,
                )
            )
        for i, falha in enumerate(hits_falhas, start=1):
            blocos_estruturados.append(
                formatar_falha_contexto(
                    indice=i,
                    codigo=falha.codigo,
                    tipo=falha.tipo.value,
                    titulo=falha.titulo,
                    descricao=falha.descricao,
                    causa=falha.causa,
                    solucao=falha.solucao,
                    reacao=falha.reacao,
                )
            )

        trechos_formatados = None
        if resultado.items:
            trechos_formatados = "\n\n".join(
                formatar_trecho_contexto(
                    indice=i,
                    titulo_documento=trecho.titulo_documento,
                    secao=trecho.secao,
                    pagina=trecho.pagina,
                    conteudo=trecho.conteudo,
                )
                for i, trecho in enumerate(resultado.items, start=1)
            )

        resposta = await self.llm.completar(
            sistema=SISTEMA_QA,
            usuario=montar_mensagem_usuario(
                pergunta=pergunta,
                estruturados_formatados="\n\n".join(blocos_estruturados) if blocos_estruturados else None,
                trechos_formatados=trechos_formatados,
            ),
        )
        return AgenteRespostaOut(
            pergunta=pergunta,
            resposta=resposta.strip(),
            citacoes=[_citacao(i, item) for i, item in enumerate(resultado.items, start=1)],
            parametros=hits_parametros,
            falhas=hits_falhas,
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
