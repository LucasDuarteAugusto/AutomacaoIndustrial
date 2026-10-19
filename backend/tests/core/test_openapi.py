import json
from collections import Counter
from pathlib import Path

from fastapi import FastAPI

from app.core.openapi import gerar_openapi, main


def _operation_ids(esquema: dict[str, object]) -> list[str]:
    caminhos = esquema["paths"]
    assert isinstance(caminhos, dict)
    return [operacao["operationId"] for metodos in caminhos.values() for operacao in metodos.values()]


def test_operation_ids_sao_unicos_e_iguais_ao_nome_da_funcao(app: FastAPI) -> None:
    ids = _operation_ids(app.openapi())
    assert [i for i, n in Counter(ids).items() if n > 1] == []
    assert {"listar_documentos", "obter_documento", "login", "perguntar", "health"} <= set(ids)
    assert not [i for i in ids if "_v1_" in i or i.endswith(("_get", "_post", "_patch", "_delete"))]


def test_gerar_openapi_funciona_sem_banco() -> None:
    esquema = gerar_openapi()
    assert esquema["openapi"].startswith("3.")
    assert "/v1/documentos" in esquema["paths"]


def test_main_grava_arquivo_json_utf8(tmp_path: Path) -> None:
    destino = tmp_path / "frontend" / "openapi.json"
    main(["--saida", str(destino)])
    conteudo = destino.read_text(encoding="utf-8")
    assert conteudo.endswith("}\n")
    esquema = json.loads(conteudo)
    assert "openapi" in esquema
    assert "\\u00" not in conteudo
