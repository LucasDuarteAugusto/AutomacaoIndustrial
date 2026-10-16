from app.agente.codigos import extrair_codigos_falha, extrair_codigos_parametro


def test_extrai_codigos_parametro() -> None:
    assert extrair_codigos_parametro("Qual o p1120 e o P0100?") == ["p1120", "P0100"]


def test_extrai_codigos_falha() -> None:
    assert extrair_codigos_falha("Apareceu F07801 e depois A0503") == ["F07801", "A0503"]


def test_nao_duplica_mesmo_codigo() -> None:
    assert extrair_codigos_parametro("p1120 e P1120") == ["p1120"]
