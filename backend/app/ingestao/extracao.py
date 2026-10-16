from dataclasses import dataclass

import fitz  # PyMuPDF


@dataclass(frozen=True, slots=True)
class PaginaExtraida:
    numero: int  # 1-based
    texto: str
    secao: str | None


def extrair_paginas(pdf: bytes) -> list[PaginaExtraida]:
    """Extrai texto por página e associa o título de seção do sumário, quando existir."""
    documento = fitz.open(stream=pdf, filetype="pdf")
    try:
        secoes_por_pagina = _mapa_secoes(documento)
        paginas: list[PaginaExtraida] = []
        for indice in range(documento.page_count):
            pagina = documento.load_page(indice)
            texto = pagina.get_text("text").strip()
            numero = indice + 1
            paginas.append(
                PaginaExtraida(
                    numero=numero,
                    texto=texto,
                    secao=secoes_por_pagina.get(numero),
                )
            )
        return paginas
    finally:
        documento.close()


def _mapa_secoes(documento: fitz.Document) -> dict[int, str]:
    """TOC do PDF: página → título da seção mais específica que começa nela."""
    try:
        toc = documento.get_toc(simple=True)
    except ValueError, RuntimeError:
        return {}
    mapa: dict[int, str] = {}
    for entrada in toc:
        if len(entrada) < 3:
            continue
        _nivel, titulo, pagina = entrada[0], entrada[1], entrada[2]
        if not isinstance(pagina, int) or pagina < 1 or not isinstance(titulo, str):
            continue
        titulo_limpo = titulo.strip()
        if titulo_limpo:
            mapa[pagina] = titulo_limpo
    return mapa
