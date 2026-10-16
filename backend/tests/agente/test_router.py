from uuid import UUID

import fitz
from httpx import AsyncClient

from tests.factories import criar_documento, criar_falha, criar_familia, criar_parametro


def _pdf(texto: str) -> bytes:
    documento = fitz.open()
    try:
        pagina = documento.new_page()
        pagina.insert_text((72, 72), texto)
        return bytes(documento.tobytes())
    finally:
        documento.close()


async def _documento_indexado(client: AsyncClient, texto: str) -> dict[str, object]:
    doc = await criar_documento(client)
    resp = await client.post(
        f"/v1/documentos/{doc['id_documento']}/arquivo",
        files={"arquivo": ("manual.pdf", _pdf(texto), "application/pdf")},
    )
    assert resp.status_code == 200, resp.text
    corpo: dict[str, object] = resp.json()
    assert corpo["status_processamento"] == "INDEXADO"
    return corpo


async def test_agente_responde_com_citacoes(client: AsyncClient) -> None:
    await _documento_indexado(
        client,
        "Parâmetro p1120 define o tempo de rampa de aceleração do inversor SINAMICS.",
    )

    resp = await client.post(
        "/v1/agente/perguntar",
        json={"pergunta": "Qual parâmetro controla o tempo de rampa?", "limit": 5},
    )
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["pergunta"] == "Qual parâmetro controla o tempo de rampa?"
    assert corpo["resposta"]
    assert corpo["modelo_llm"] == "fake-llm"
    assert corpo["trechos_consultados"] >= 1
    assert len(corpo["citacoes"]) == corpo["trechos_consultados"]
    primeira = corpo["citacoes"][0]
    assert primeira["indice"] == 1
    assert primeira["id_documento"]
    assert primeira["titulo_documento"]
    assert "rampa" in primeira["trecho"].lower() or "p1120" in primeira["trecho"].lower()


async def test_agente_sem_trechos_nao_chama_llm_com_alucinacao(client: AsyncClient) -> None:
    resp = await client.post(
        "/v1/agente/perguntar",
        json={
            "pergunta": "xyzzy-termo-inexistente-12345",
            "id_familia": str(UUID(int=1)),
            "limit": 5,
        },
    )
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["citacoes"] == []
    assert corpo["parametros"] == []
    assert corpo["falhas"] == []
    assert corpo["trechos_consultados"] == 0
    assert "não encontrei" in corpo["resposta"].lower()


async def test_agente_pergunta_vazia_retorna_422(client: AsyncClient) -> None:
    resp = await client.post("/v1/agente/perguntar", json={"pergunta": "   "})
    assert resp.status_code == 422


async def test_agente_exige_autenticacao(client_sem_auth: AsyncClient) -> None:
    resp = await client_sem_auth.post("/v1/agente/perguntar", json={"pergunta": "o que é p1120?"})
    assert resp.status_code == 401


async def test_agente_usa_parametro_estruturado_sem_trecho(client: AsyncClient) -> None:
    familia = await criar_familia(client)
    await criar_parametro(
        client,
        id_familia=familia["id_familia"],
        codigo="p1120",
        descricao="Tempo de rampa de aceleração em segundos",
        unidade="s",
        valor_padrao="10",
    )

    resp = await client.post(
        "/v1/agente/perguntar",
        json={
            "pergunta": "O que significa o parâmetro p1120?",
            "id_familia": familia["id_familia"],
            "limit": 5,
        },
    )
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["trechos_consultados"] == 0
    assert len(corpo["parametros"]) == 1
    assert corpo["parametros"][0]["codigo"].lower() == "p1120"
    assert corpo["resposta"]


async def test_agente_usa_falha_estruturada(client: AsyncClient) -> None:
    familia = await criar_familia(client)
    await criar_falha(
        client,
        id_familia=familia["id_familia"],
        codigo="F07801",
        titulo="Sobrecorrente",
        causa="Carga excessiva",
        solucao="Verificar motor",
    )

    resp = await client.post(
        "/v1/agente/perguntar",
        json={"pergunta": "O que é F07801?", "id_familia": familia["id_familia"]},
    )
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert len(corpo["falhas"]) == 1
    assert corpo["falhas"][0]["codigo"].upper() == "F07801"
