"""Extração de códigos de parâmetro e falha a partir da pergunta do técnico."""

import re

# p1120, P0100, r0063 — códigos típicos Siemens / inversores
_RE_PARAMETRO = re.compile(r"\b[pPrR]\d{3,5}\b")
# F07801, A0503, f7210 — falhas e alarmes
_RE_FALHA = re.compile(r"\b[fFaA]\d{4,6}\b")


def extrair_codigos_parametro(texto: str) -> list[str]:
    vistos: set[str] = set()
    ordem: list[str] = []
    for match in _RE_PARAMETRO.finditer(texto):
        codigo = match.group(0)
        chave = codigo.lower()
        if chave not in vistos:
            vistos.add(chave)
            ordem.append(codigo)
    return ordem


def extrair_codigos_falha(texto: str) -> list[str]:
    vistos: set[str] = set()
    ordem: list[str] = []
    for match in _RE_FALHA.finditer(texto):
        codigo = match.group(0)
        chave = codigo.lower()
        if chave not in vistos:
            vistos.add(chave)
            ordem.append(codigo)
    return ordem
