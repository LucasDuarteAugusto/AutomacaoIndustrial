from app.ingestao.chunking import chunkar_paginas
from app.ingestao.extracao import PaginaExtraida
from app.trechos.models import TipoConteudo


def test_chunkar_respeita_limite_e_pagina() -> None:
    paginas = [
        PaginaExtraida(1, "Primeiro parágrafo.\n\nSegundo parágrafo.", "Introdução"),
        PaginaExtraida(2, "Terceiro parágrafo longo o suficiente.", None),
    ]
    trechos = chunkar_paginas(paginas, tamanho_max_chars=200)
    assert trechos
    assert trechos[0].pagina == 1
    assert trechos[0].secao == "Introdução"
    assert all(len(t.conteudo) <= 200 for t in trechos)


def test_chunkar_detecta_tabela() -> None:
    texto = "a|b|c\n1|2|3\n4|5|6\n7|8|9"
    trechos = chunkar_paginas([PaginaExtraida(1, texto, None)], tamanho_max_chars=500)
    assert len(trechos) == 1
    assert trechos[0].tipo_conteudo == TipoConteudo.TABELA
