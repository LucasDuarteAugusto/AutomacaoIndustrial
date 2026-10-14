from uuid import uuid4

from httpx import AsyncClient

from tests.factories import criar_equipamento, criar_fabricante, criar_familia, id_tipo


async def test_criar_familia_retorna_201(client: AsyncClient) -> None:
    fabricante = await criar_fabricante(client)
    tipo = await id_tipo(client, "SOFT_STARTER")

    resp = await client.post(
        "/v1/familias",
        json={"id_fabricante": fabricante["id_fabricante"], "id_tipo_equipamento": tipo, "nome": "SIRIUS 3RW55"},
    )

    assert resp.status_code == 201
    corpo = resp.json()
    assert corpo["nome"] == "SIRIUS 3RW55"
    assert corpo["id_tipo_equipamento"] == tipo


async def test_criar_familia_com_fabricante_inexistente_retorna_422(client: AsyncClient) -> None:
    resp = await client.post(
        "/v1/familias",
        json={"id_fabricante": str(uuid4()), "id_tipo_equipamento": await id_tipo(client), "nome": "CFW500"},
    )

    assert resp.status_code == 422
    assert "Fabricante" in resp.json()["detail"]


async def test_criar_familia_com_tipo_inexistente_retorna_422(client: AsyncClient) -> None:
    fabricante = await criar_fabricante(client)

    resp = await client.post(
        "/v1/familias",
        json={"id_fabricante": fabricante["id_fabricante"], "id_tipo_equipamento": str(uuid4()), "nome": "CFW500"},
    )

    assert resp.status_code == 422


async def test_criar_familia_com_nome_repetido_no_mesmo_fabricante_retorna_409(client: AsyncClient) -> None:
    familia = await criar_familia(client, nome="SINAMICS G120")

    resp = await client.post(
        "/v1/familias",
        json={
            "id_fabricante": familia["id_fabricante"],
            "id_tipo_equipamento": familia["id_tipo_equipamento"],
            "nome": "sinamics g120",
        },
    )

    assert resp.status_code == 409


async def test_criar_familia_com_mesmo_nome_em_outro_fabricante_retorna_201(client: AsyncClient) -> None:
    await criar_familia(client, nome="Série X")

    familia = await criar_familia(client, nome="Série X")

    assert familia["nome"] == "Série X"


async def test_listar_familias_filtra_por_fabricante_e_tipo(client: AsyncClient) -> None:
    fabricante = await criar_fabricante(client)
    inversor = await id_tipo(client, "INVERSOR")
    soft = await id_tipo(client, "SOFT_STARTER")
    await criar_familia(client, id_fabricante=fabricante["id_fabricante"], id_tipo_equipamento=inversor, nome="G120")
    await criar_familia(client, id_fabricante=fabricante["id_fabricante"], id_tipo_equipamento=soft, nome="3RW55")
    await criar_familia(client, id_tipo_equipamento=inversor)

    resp = await client.get(
        "/v1/familias", params={"id_fabricante": fabricante["id_fabricante"], "id_tipo_equipamento": inversor}
    )

    assert resp.status_code == 200
    assert [f["nome"] for f in resp.json()["items"]] == ["G120"]


async def test_alterar_familia_para_nome_existente_no_fabricante_retorna_409(client: AsyncClient) -> None:
    existente = await criar_familia(client, nome="G120")
    outra = await criar_familia(client, id_fabricante=existente["id_fabricante"])

    resp = await client.patch(f"/v1/familias/{outra['id_familia']}", json={"nome": "G120"})

    assert resp.status_code == 409


async def test_alterar_familia_inexistente_retorna_404(client: AsyncClient) -> None:
    resp = await client.patch(f"/v1/familias/{uuid4()}", json={"nome": "Nova"})

    assert resp.status_code == 404


async def test_excluir_familia_com_equipamentos_retorna_409(client: AsyncClient) -> None:
    equipamento = await criar_equipamento(client)

    resp = await client.delete(f"/v1/familias/{equipamento['id_familia']}")

    assert resp.status_code == 409


async def test_excluir_familia_sem_vinculos_retorna_204(client: AsyncClient) -> None:
    familia = await criar_familia(client)

    resp = await client.delete(f"/v1/familias/{familia['id_familia']}")

    assert resp.status_code == 204
