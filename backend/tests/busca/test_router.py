from uuid import UUID

import fitz
from httpx import AsyncClient

from tests.factories import criar_documento, criar_familia


def _pdf(texto: str) -> bytes:
    documento = fitz.open()
    try:
        pagina = documento.new_page()
        pagina.insert_text((72, 72), texto)
        return bytes(documento.tobytes())
    finally:
        documento.close()


async def _documento_indexado(client: AsyncClient, texto: str, **campos: object) -> dict[str, object]:
    doc = await criar_documento(client, **campos)
    resp = await client.post(
        f"/v1/documentos/{doc['id_documento']}/arquivo",
        files={"arquivo": ("manual.pdf", _pdf(texto), "application/pdf")},
    )
    assert resp.status_code == 200, resp.text
    corpo: dict[str, object] = resp.json()
    assert corpo["status_processamento"] == "INDEXADO"
    return corpo


async def test_busca_retorna_trecho_relevante(client: AsyncClient) -> None:
    await _documento_indexado(
        client,
        "Parâmetro p1120 define o tempo de rampa de aceleração do inversor SINAMICS.",
    )

    resp = await client.post("/v1/busca", json={"consulta": "tempo de rampa p1120", "limit": 5})
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["consulta"] == "tempo de rampa p1120"
    assert corpo["total"] >= 1
    assert any("rampa" in item["conteudo"].lower() or "p1120" in item["conteudo"].lower() for item in corpo["items"])
    primeiro = corpo["items"][0]
    assert primeiro["score"] > 0
    assert primeiro["id_documento"]
    assert primeiro["titulo_documento"]


async def test_busca_filtra_por_familia(client: AsyncClient) -> None:
    familia_a = await criar_familia(client)
    familia_b = await criar_familia(client)
    await _documento_indexado(
        client,
        "Manual da família A: falha F07801 sobrecorrente.",
        ids_familias=[familia_a["id_familia"]],
    )
    await _documento_indexado(
        client,
        "Manual da família B: parâmetro de torque.",
        ids_familias=[familia_b["id_familia"]],
    )

    resp = await client.post(
        "/v1/busca",
        json={
            "consulta": "falha F07801 sobrecorrente",
            "id_familia": familia_a["id_familia"],
            "limit": 10,
        },
    )
    assert resp.status_code == 200, resp.text
    ids = {item["id_documento"] for item in resp.json()["items"]}
    # todos os hits devem ser da família A (documento com F07801)
    for id_documento in ids:
        doc = (await client.get(f"/v1/documentos/{id_documento}")).json()
        assert any(f["id_familia"] == familia_a["id_familia"] for f in doc["familias"])


async def test_busca_consulta_vazia_retorna_422(client: AsyncClient) -> None:
    resp = await client.post("/v1/busca", json={"consulta": "   "})
    assert resp.status_code == 422


async def test_busca_sem_resultados_retorna_lista_vazia(client: AsyncClient) -> None:
    resp = await client.post(
        "/v1/busca",
        json={"consulta": "xyzzy-termo-inexistente-12345", "id_familia": str(UUID(int=1))},
    )
    assert resp.status_code == 200
    assert resp.json()["items"] == []
    assert resp.json()["total"] == 0
