from app.agente.prompts import formatar_trecho_contexto, montar_mensagem_usuario


def test_formatar_trecho_inclui_indice_e_localizacao() -> None:
    texto = formatar_trecho_contexto(
        indice=2,
        titulo_documento="Manual G120",
        secao="3.1 Rampa",
        pagina=42,
        conteudo="p1120 = tempo de rampa",
    )
    assert texto.startswith("[2]")
    assert "Manual G120" in texto
    assert "seção: 3.1 Rampa" in texto
    assert "página: 42" in texto
    assert "p1120 = tempo de rampa" in texto


def test_montar_mensagem_usuario_contem_pergunta_e_trechos() -> None:
    msg = montar_mensagem_usuario(
        pergunta="tempo de rampa?",
        estruturados_formatados="[P1] p1120",
        trechos_formatados="[1] trecho",
    )
    assert "tempo de rampa?" in msg
    assert "[P1] p1120" in msg
    assert "[1] trecho" in msg
