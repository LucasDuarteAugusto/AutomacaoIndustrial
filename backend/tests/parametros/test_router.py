from httpx import AsyncClient

from tests.factories import criar_familia, criar_parametro


async def test_criar_e_obter_parametro(client: AsyncClient) -> None:
    familia = await criar_familia(client)
    resp = await client.post(
        "/v1/parametros",
        json={
            "id_familia": familia["id_familia"],
            "codigo": "p1120",
            "nome": "Tempo de rampa",
            "descricao": "Tempo de rampa de aceleração",
            "unidade": "s",
            "valor_min": 0,
            "valor_max": 999,
            "valor_padrao": "10",
            "grupo": "Ramp generator",
        },
    )
    assert resp.status_code == 201, resp.text
    corpo = resp.json()
    assert corpo["codigo"] == "p1120"
    assert corpo["unidade"] == "s"

    obtido = await client.get(f"/v1/parametros/{corpo['id_parametro']}")
    assert obtido.status_code == 200
    assert obtido.json()["nome"] == "Tempo de rampa"


async def test_parametro_duplicado_mesmo_escopo_retorna_409(client: AsyncClient) -> None:
    familia = await criar_familia(client)
    await criar_parametro(client, id_familia=familia["id_familia"], codigo="p1120")
    resp = await client.post(
        "/v1/parametros",
        json={
            "id_familia": familia["id_familia"],
            "codigo": "P1120",
            "descricao": "Duplicado",
        },
    )
    assert resp.status_code == 409


async def test_listar_parametros_filtra_por_codigo(client: AsyncClient) -> None:
    familia = await criar_familia(client)
    await criar_parametro(client, id_familia=familia["id_familia"], codigo="p1120")
    await criar_parametro(client, id_familia=familia["id_familia"], codigo="p1082")

    resp = await client.get("/v1/parametros", params={"id_familia": familia["id_familia"], "codigo": "p1120"})
    assert resp.status_code == 200
    assert [i["codigo"].lower() for i in resp.json()["items"]] == ["p1120"]
