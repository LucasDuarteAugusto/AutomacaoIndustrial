from uuid import uuid4

from httpx import AsyncClient

from tests.factories import criar_documento, criar_equipamento, criar_familia


async def test_criar_documento_com_familia_e_equipamento_retorna_201(client: AsyncClient) -> None:
    equipamento = await criar_equipamento(client)

    resp = await client.post(
        "/v1/documentos",
        json={
            "titulo": "SINAMICS G120 - Lista de parâmetros",
            "tipo_documento": "LISTA_PARAMETROS",
            "idioma": "pt-BR",
            "ids_familias": [equipamento["id_familia"]],
            "ids_equipamentos": [equipamento["id_equipamento"], equipamento["id_equipamento"]],
        },
    )

    assert resp.status_code == 201
    corpo = resp.json()
    assert corpo["status_processamento"] == "PENDENTE"
    assert [f["id_familia"] for f in corpo["familias"]] == [equipamento["id_familia"]]
    assert [e["id_equipamento"] for e in corpo["equipamentos"]] == [equipamento["id_equipamento"]]
    assert corpo["hash_sha256"] is None


async def test_criar_documento_sem_familias_retorna_422(client: AsyncClient) -> None:
    resp = await client.post(
        "/v1/documentos",
        json={"titulo": "Manual", "tipo_documento": "DATASHEET", "idioma": "en", "ids_familias": []},
    )

    assert resp.status_code == 422


async def test_criar_documento_com_tipo_invalido_retorna_422(client: AsyncClient) -> None:
    familia = await criar_familia(client)

    resp = await client.post(
        "/v1/documentos",
        json={"titulo": "Manual", "tipo_documento": "LIVRO", "idioma": "en", "ids_familias": [familia["id_familia"]]},
    )

    assert resp.status_code == 422


async def test_criar_documento_com_familia_inexistente_retorna_422(client: AsyncClient) -> None:
    resp = await client.post(
        "/v1/documentos",
        json={"titulo": "Manual", "tipo_documento": "DATASHEET", "idioma": "en", "ids_familias": [str(uuid4())]},
    )

    assert resp.status_code == 422
    assert "Família" in resp.json()["detail"]


async def test_criar_documento_com_equipamento_de_outra_familia_retorna_422(client: AsyncClient) -> None:
    familia = await criar_familia(client)
    equipamento_de_outra = await criar_equipamento(client)

    resp = await client.post(
        "/v1/documentos",
        json={
            "titulo": "Datasheet",
            "tipo_documento": "DATASHEET",
            "idioma": "en",
            "ids_familias": [familia["id_familia"]],
            "ids_equipamentos": [equipamento_de_outra["id_equipamento"]],
        },
    )

    assert resp.status_code == 422
    assert equipamento_de_outra["codigo_pedido"] in resp.json()["detail"]


async def test_listar_documentos_filtra_por_familia_e_idioma(client: AsyncClient) -> None:
    familia = await criar_familia(client)
    alvo = await criar_documento(client, ids_familias=[familia["id_familia"]], idioma="en")
    await criar_documento(client, ids_familias=[familia["id_familia"]], idioma="pt-BR")
    await criar_documento(client, idioma="en")

    resp = await client.get("/v1/documentos", params={"id_familia": familia["id_familia"], "idioma": "en"})

    assert resp.status_code == 200
    assert [d["id_documento"] for d in resp.json()["items"]] == [alvo["id_documento"]]


async def test_listar_documentos_filtra_por_equipamento(client: AsyncClient) -> None:
    equipamento = await criar_equipamento(client)
    alvo = await criar_documento(
        client, ids_familias=[equipamento["id_familia"]], ids_equipamentos=[equipamento["id_equipamento"]]
    )
    await criar_documento(client, ids_familias=[equipamento["id_familia"]])

    resp = await client.get("/v1/documentos", params={"id_equipamento": equipamento["id_equipamento"]})

    assert [d["id_documento"] for d in resp.json()["items"]] == [alvo["id_documento"]]


async def test_alterar_documento_substitui_familias_e_mantem_demais_campos(client: AsyncClient) -> None:
    documento = await criar_documento(client)
    nova_familia = await criar_familia(client)

    resp = await client.patch(
        f"/v1/documentos/{documento['id_documento']}", json={"ids_familias": [nova_familia["id_familia"]]}
    )

    assert resp.status_code == 200
    corpo = resp.json()
    assert [f["id_familia"] for f in corpo["familias"]] == [nova_familia["id_familia"]]
    assert corpo["titulo"] == documento["titulo"]


async def test_alterar_documento_trocando_familia_sem_remover_equipamento_retorna_422(client: AsyncClient) -> None:
    equipamento = await criar_equipamento(client)
    documento = await criar_documento(
        client, ids_familias=[equipamento["id_familia"]], ids_equipamentos=[equipamento["id_equipamento"]]
    )
    nova_familia = await criar_familia(client)

    resp = await client.patch(
        f"/v1/documentos/{documento['id_documento']}", json={"ids_familias": [nova_familia["id_familia"]]}
    )

    assert resp.status_code == 422


async def test_alterar_documento_com_titulo_nulo_retorna_422(client: AsyncClient) -> None:
    documento = await criar_documento(client)

    resp = await client.patch(f"/v1/documentos/{documento['id_documento']}", json={"titulo": None})

    assert resp.status_code == 422


async def test_excluir_familia_vinculada_a_documento_retorna_409(client: AsyncClient) -> None:
    documento = await criar_documento(client)

    resp = await client.delete(f"/v1/familias/{documento['familias'][0]['id_familia']}")

    assert resp.status_code == 409


async def test_excluir_documento_libera_exclusao_da_familia(client: AsyncClient) -> None:
    documento = await criar_documento(client)
    id_familia = documento["familias"][0]["id_familia"]

    resp = await client.delete(f"/v1/documentos/{documento['id_documento']}")

    assert resp.status_code == 204
    assert (await client.get(f"/v1/documentos/{documento['id_documento']}")).status_code == 404
    assert (await client.delete(f"/v1/familias/{id_familia}")).status_code == 204
