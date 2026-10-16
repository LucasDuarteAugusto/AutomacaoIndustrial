from dataclasses import dataclass

from app.ingestao.extracao import PaginaExtraida
from app.trechos.models import TipoConteudo


@dataclass(frozen=True, slots=True)
class TrechoCandidato:
    conteudo: str
    secao: str | None
    pagina: int | None
    tipo_conteudo: TipoConteudo


def chunkar_paginas(
    paginas: list[PaginaExtraida],
    *,
    tamanho_max_chars: int = 2500,
) -> list[TrechoCandidato]:
    """Agrupa parágrafos em trechos sem overlap, respeitando limite de caracteres."""
    if tamanho_max_chars < 200:
        msg = "tamanho_max_chars deve ser >= 200"
        raise ValueError(msg)

    candidatos: list[TrechoCandidato] = []
    buffer: list[str] = []
    chars = 0
    secao_atual: str | None = None
    pagina_inicio: int | None = None
    secao_propagada: str | None = None

    def _flush() -> None:
        nonlocal buffer, chars, secao_atual, pagina_inicio
        if not buffer:
            return
        texto = "\n\n".join(buffer).strip()
        if texto:
            candidatos.append(
                TrechoCandidato(
                    conteudo=texto,
                    secao=secao_atual,
                    pagina=pagina_inicio,
                    tipo_conteudo=_inferir_tipo(texto),
                )
            )
        buffer = []
        chars = 0
        secao_atual = None
        pagina_inicio = None

    for pagina in paginas:
        if pagina.secao:
            secao_propagada = pagina.secao
        if not pagina.texto:
            continue
        for paragrafo in _paragrafos(pagina.texto):
            tamanho = len(paragrafo)
            if buffer and chars + tamanho + 2 > tamanho_max_chars:
                _flush()
            if not buffer:
                secao_atual = secao_propagada
                pagina_inicio = pagina.numero
            if tamanho > tamanho_max_chars:
                _flush()
                for pedaco in _partir(paragrafo, tamanho_max_chars):
                    candidatos.append(
                        TrechoCandidato(
                            conteudo=pedaco,
                            secao=secao_propagada,
                            pagina=pagina.numero,
                            tipo_conteudo=_inferir_tipo(pedaco),
                        )
                    )
                continue
            buffer.append(paragrafo)
            chars += tamanho + (2 if len(buffer) > 1 else 0)

    _flush()
    return candidatos


def _paragrafos(texto: str) -> list[str]:
    blocos = [b.strip() for b in texto.replace("\r\n", "\n").split("\n\n")]
    return [b for b in blocos if b]


def _partir(texto: str, tamanho: int) -> list[str]:
    return [texto[i : i + tamanho] for i in range(0, len(texto), tamanho)]


def _inferir_tipo(texto: str) -> TipoConteudo:
    linhas = [ln for ln in texto.splitlines() if ln.strip()]
    if len(linhas) >= 3:
        com_separador = sum(1 for ln in linhas if ln.count("|") >= 2 or ln.count("\t") >= 2)
        if com_separador / len(linhas) >= 0.5:
            return TipoConteudo.TABELA
    return TipoConteudo.TEXTO
