SISTEMA_QA = """\
Você é um assistente técnico de comissionamento de acionamentos industriais \
(relés SIMOCODE, soft starters e inversores).

Priorize os registros estruturados de parâmetros ([P1], [P2], …) e falhas ([F1], [F2], …) \
quando existirem — eles são a fonte canônica para códigos, faixas, causas e soluções.
Use os trechos de documentação ([1], [2], …) para complementar o contexto.

Responda APENAS com base no contexto fornecido.
Se a informação não estiver no contexto, diga claramente que não encontrou \
na documentação recuperada — não invente parâmetros, códigos de falha nem valores.

Cite as fontes no texto com os marcadores correspondentes ([P1], [F1], [1], …).
Seja objetivo e use português do Brasil.
"""


def montar_mensagem_usuario(
    *,
    pergunta: str,
    estruturados_formatados: str | None,
    trechos_formatados: str | None,
) -> str:
    partes = [f"Pergunta do usuário:\n{pergunta}"]
    if estruturados_formatados:
        partes.append(f"Dados estruturados (parâmetros e falhas):\n{estruturados_formatados}")
    if trechos_formatados:
        partes.append(f"Trechos da documentação:\n{trechos_formatados}")
    partes.append("Resposta (com citações quando aplicável):")
    return "\n\n".join(partes)


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


def formatar_parametro_contexto(
    *,
    indice: int,
    codigo: str,
    nome: str | None,
    descricao: str,
    unidade: str | None,
    valor_min: object,
    valor_max: object,
    valor_padrao: str | None,
    grupo: str | None,
) -> str:
    linhas = [f"[P{indice}] Parâmetro {codigo}" + (f" — {nome}" if nome else "")]
    linhas.append(descricao)
    detalhes = []
    if unidade:
        detalhes.append(f"unidade: {unidade}")
    if valor_min is not None or valor_max is not None:
        detalhes.append(f"faixa: {valor_min} … {valor_max}")
    if valor_padrao:
        detalhes.append(f"padrão: {valor_padrao}")
    if grupo:
        detalhes.append(f"grupo: {grupo}")
    if detalhes:
        linhas.append("; ".join(detalhes))
    return "\n".join(linhas)


def formatar_falha_contexto(
    *,
    indice: int,
    codigo: str,
    tipo: str,
    titulo: str,
    descricao: str | None,
    causa: str | None,
    solucao: str | None,
    reacao: str | None,
) -> str:
    linhas = [f"[F{indice}] {tipo} {codigo} — {titulo}"]
    if descricao:
        linhas.append(descricao)
    if causa:
        linhas.append(f"Causa: {causa}")
    if solucao:
        linhas.append(f"Solução: {solucao}")
    if reacao:
        linhas.append(f"Reação: {reacao}")
    return "\n".join(linhas)


RESPOSTA_SEM_CONTEXTOS = (
    "Não encontrei trechos nem registros estruturados relevantes para esta pergunta. "
    "Tente reformular, informar a família/equipamento, ou confirmar se o manual e as "
    "tabelas de parâmetros/falhas foram cadastrados."
)
