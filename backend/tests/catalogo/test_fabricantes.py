from uuid import uuid4

from httpx import AsyncClient

from tests.factories import criar_fabricante, criar_familia


async def test_criar_fabricante_retorna_201(client: AsyncClient) -> None:
    resp = await client.post("/v1/fabricantes", json={"nome": "  Siemens  ", "site": "https://siemens.com"})

    assert resp.status_code == 201
    corpo = resp.json()
    assert corpo["nome"] == "Siemens"
    assert corpo["ativo"] is True
    assert corpo["id_fabricante"]
    assert corpo["created_at"]


async def test_criar_fabricante_com_nome_duplicado_ignorando_caixa_retorna_409(client: AsyncClient) -> None:
    await criar_fabricante(client, nome="WEG")

    resp = await client.post("/v1/fabricantes", json={"nome": "weg"})

    assert resp.status_code == 409
    assert resp.headers["content-type"] == "application/problem+json"


async def test_criar_fabricante_com_nome_vazio_retorna_422(client: AsyncClient) -> None:
    resp = await client.post("/v1/fabricantes", json={"nome": "   "})

    assert resp.status_code == 422


async def test_criar_fabricante_com_campo_desconhecido_retorna_422(client: AsyncClient) -> None:
    resp = await client.post("/v1/fabricantes", json={"nome": "ABB", "pais": "Suíça"})

    assert resp.status_code == 422


async def test_listar_fabricantes_filtra_por_busca_e_pagina(client: AsyncClient) -> None:
    for nome in ("Danfoss", "Schneider Electric", "Schmersal"):
        await criar_fabricante(client, nome=nome)

    resp = await client.get("/v1/fabricantes", params={"busca": "sch", "limit": 1})

    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["total"] == 2
    assert [f["nome"] for f in corpo["items"]] == ["Schmersal"]


async def test_listar_fabricantes_com_limit_acima_do_maximo_retorna_422(client: AsyncClient) -> None:
    resp = await client.get("/v1/fabricantes", params={"limit": 101})

    assert resp.status_code == 422


async def test_obter_fabricante_inexistente_retorna_404(client: AsyncClient) -> None:
    resp = await client.get(f"/v1/fabricantes/{uuid4()}")

    assert resp.status_code == 404


async def test_alterar_fabricante_atualiza_apenas_campos_enviados(client: AsyncClient) -> None:
    fabricante = await criar_fabricante(client, site="https://antigo.com")

    resp = await client.patch(f"/v1/fabricantes/{fabricante['id_fabricante']}", json={"ativo": False})

    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["ativo"] is False
    assert corpo["site"] == "https://antigo.com"
    assert corpo["nome"] == fabricante["nome"]


async def test_alterar_fabricante_com_nome_nulo_retorna_422(client: AsyncClient) -> None:
    fabricante = await criar_fabricante(client)

    resp = await client.patch(f"/v1/fabricantes/{fabricante['id_fabricante']}", json={"nome": None})

    assert resp.status_code == 422


async def test_alterar_fabricante_para_nome_de_outro_retorna_409(client: AsyncClient) -> None:
    await criar_fabricante(client, nome="Rockwell")
    fabricante = await criar_fabricante(client)

    resp = await client.patch(f"/v1/fabricantes/{fabricante['id_fabricante']}", json={"nome": "ROCKWELL"})

    assert resp.status_code == 409


async def test_excluir_fabricante_sem_familias_retorna_204(client: AsyncClient) -> None:
    fabricante = await criar_fabricante(client)

    resp = await client.delete(f"/v1/fabricantes/{fabricante['id_fabricante']}")

    assert resp.status_code == 204
    assert (await client.get(f"/v1/fabricantes/{fabricante['id_fabricante']}")).status_code == 404


async def test_excluir_fabricante_com_familias_retorna_409(client: AsyncClient) -> None:
    fabricante = await criar_fabricante(client)
    await criar_familia(client, id_fabricante=fabricante["id_fabricante"])

    resp = await client.delete(f"/v1/fabricantes/{fabricante['id_fabricante']}")

    assert resp.status_code == 409
    assert "Desative" in resp.json()["detail"]
