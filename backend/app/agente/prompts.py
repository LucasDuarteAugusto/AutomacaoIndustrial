SISTEMA_QA = """\
Você é um assistente técnico de comissionamento de acionamentos industriais \
(relés SIMOCODE, soft starters e inversores).

Responda APENAS com base nos trechos numerados fornecidos no contexto.
Se a informação não estiver nos trechos, diga claramente que não encontrou \
na documentação recuperada — não invente parâmetros, códigos de falha nem valores.

Cite as fontes no texto usando colchetes, por exemplo [1] ou [2], \
correspondentes aos números dos trechos.
Seja objetivo e use português do Brasil.
"""


def montar_mensagem_usuario(*, pergunta: str, trechos_formatados: str) -> str:
    return (
        f"Pergunta do usuário:\n{pergunta}\n\n"
        f"Trechos da documentação:\n{trechos_formatados}\n\n"
        "Resposta (com citações [n] quando aplicável):"
    )


def formatar_trecho_contexto(
    *,
    indice: int,
    titulo_documento: str,
    secao: str | None,
    pagina: int | None,
    conteudo: str,
) -> str:
    local = []
    if secao:
        local.append(f"seção: {secao}")
    if pagina is not None:
        local.append(f"página: {pagina}")
    meta = f" ({'; '.join(local)})" if local else ""
    return f"[{indice}] Documento: {titulo_documento}{meta}\n{conteudo}"


RESPOSTA_SEM_CONTEXTOS = (
    "Não encontrei trechos relevantes na documentação indexada para esta pergunta. "
    "Tente reformular, verificar filtros (família/equipamento) ou confirmar se o "
    "manual foi enviado e processado."
)
