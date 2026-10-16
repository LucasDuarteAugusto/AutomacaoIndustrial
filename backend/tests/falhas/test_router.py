from httpx import AsyncClient

from tests.factories import criar_fabricante, criar_falha, criar_familia


async def test_criar_e_listar_falha(client: AsyncClient) -> None:
    familia = await criar_familia(client)
    resp = await client.post(
        "/v1/falhas",
        json={
            "id_familia": familia["id_familia"],
            "codigo": "F07801",
            "tipo": "FALHA",
            "titulo": "Sobrecorrente",
            "causa": "Carga excessiva ou curto",
            "solucao": "Verificar motor e cabo",
            "reacao": "OFF2",
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["codigo"] == "F07801"

    lista = await client.get("/v1/falhas", params={"codigo": "F07801", "id_familia": familia["id_familia"]})
    assert lista.status_code == 200
    assert lista.json()["total"] == 1
    assert lista.json()["items"][0]["titulo"] == "Sobrecorrente"


async def test_falha_duplicada_retorna_409(client: AsyncClient) -> None:
    familia = await criar_familia(client)
    await criar_falha(client, id_familia=familia["id_familia"], codigo="F07801")
    resp = await client.post(
        "/v1/falhas",
        json={
            "id_familia": familia["id_familia"],
            "codigo": "f07801",
            "tipo": "FALHA",
            "titulo": "Outro título",
        },
    )
    assert resp.status_code == 409


async def test_falha_mesmo_codigo_em_outra_familia_ok(client: AsyncClient) -> None:
    await criar_falha(client, codigo="F07801")
    outra = await criar_familia(client, id_fabricante=(await criar_fabricante(client))["id_fabricante"])
    resp = await client.post(
        "/v1/falhas",
        json={
            "id_familia": outra["id_familia"],
            "codigo": "F07801",
            "tipo": "FALHA",
            "titulo": "Sobrecorrente em outra família",
        },
    )
    assert resp.status_code == 201, resp.text
