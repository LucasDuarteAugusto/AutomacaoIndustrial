from uuid import uuid4

from httpx import AsyncClient

from tests.factories import criar_equipamento, criar_familia


async def test_criar_equipamento_retorna_201_com_valores_numericos(client: AsyncClient) -> None:
    familia = await criar_familia(client)

    resp = await client.post(
        "/v1/equipamentos",
        json={
            "id_familia": familia["id_familia"],
            "codigo_pedido": "6SL3210-1KE21-3UF1",
            "nome": "PM240-2 5,5 kW 400 V",
            "potencia_kw": 5.5,
            "tensao_nominal_v": 400,
            "corrente_nominal_a": "13.2",
        },
    )

    assert resp.status_code == 201
    corpo = resp.json()
    assert corpo["potencia_kw"] == 5.5
    assert corpo["corrente_nominal_a"] == 13.2
    assert corpo["tensao_nominal_v"] == 400


async def test_criar_equipamento_com_familia_inexistente_retorna_422(client: AsyncClient) -> None:
    resp = await client.post(
        "/v1/equipamentos", json={"id_familia": str(uuid4()), "codigo_pedido": "X-1", "nome": "Modelo X"}
    )

    assert resp.status_code == 422


async def test_criar_equipamento_com_potencia_negativa_retorna_422(client: AsyncClient) -> None:
    familia = await criar_familia(client)

    resp = await client.post(
        "/v1/equipamentos",
        json={"id_familia": familia["id_familia"], "codigo_pedido": "X-1", "nome": "Modelo X", "potencia_kw": -1},
    )

    assert resp.status_code == 422


async def test_criar_equipamento_com_codigo_repetido_na_familia_retorna_409(client: AsyncClient) -> None:
    equipamento = await criar_equipamento(client, codigo_pedido="3RW5524-1HA14")

    resp = await client.post(
        "/v1/equipamentos",
        json={"id_familia": equipamento["id_familia"], "codigo_pedido": "3rw5524-1ha14", "nome": "Outro"},
    )

    assert resp.status_code == 409


async def test_listar_equipamentos_busca_por_codigo_ou_nome(client: AsyncClient) -> None:
    familia = await criar_familia(client)
    await criar_equipamento(client, id_familia=familia["id_familia"], codigo_pedido="6SL3210-1KE21", nome="PM240")
    await criar_equipamento(client, id_familia=familia["id_familia"], codigo_pedido="6SL3224-0BE", nome="PM250 G")
    await criar_equipamento(client, id_familia=familia["id_familia"], codigo_pedido="3RW55", nome="Soft")

    resp = await client.get("/v1/equipamentos", params={"id_familia": familia["id_familia"], "busca": "6sl"})

    assert resp.status_code == 200
    assert [e["codigo_pedido"] for e in resp.json()["items"]] == ["6SL3210-1KE21", "6SL3224-0BE"]


async def test_alterar_equipamento_atualiza_updated_at(client: AsyncClient) -> None:
    equipamento = await criar_equipamento(client)

    resp = await client.patch(f"/v1/equipamentos/{equipamento['id_equipamento']}", json={"potencia_kw": 7.5})

    assert resp.status_code == 200
    assert resp.json()["potencia_kw"] == 7.5
    assert resp.json()["updated_at"] >= equipamento["updated_at"]


async def test_excluir_equipamento_retorna_204(client: AsyncClient) -> None:
    equipamento = await criar_equipamento(client)

    resp = await client.delete(f"/v1/equipamentos/{equipamento['id_equipamento']}")

    assert resp.status_code == 204
    assert (await client.get(f"/v1/equipamentos/{equipamento['id_equipamento']}")).status_code == 404
