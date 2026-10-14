from uuid import uuid4

from httpx import AsyncClient


async def test_listar_tipos_retorna_os_tipos_iniciais(client: AsyncClient) -> None:
    resp = await client.get("/v1/tipos-equipamento")

    assert resp.status_code == 200
    codigos = {t["codigo"] for t in resp.json()["items"]}
    assert {"RELE_GERENCIAMENTO", "SOFT_STARTER", "INVERSOR"} <= codigos


async def test_obter_tipo_existente_retorna_200(client: AsyncClient) -> None:
    tipo = (await client.get("/v1/tipos-equipamento")).json()["items"][0]

    resp = await client.get(f"/v1/tipos-equipamento/{tipo['id_tipo_equipamento']}")

    assert resp.status_code == 200
    assert resp.json() == tipo


async def test_obter_tipo_inexistente_retorna_404(client: AsyncClient) -> None:
    resp = await client.get(f"/v1/tipos-equipamento/{uuid4()}")

    assert resp.status_code == 404
    assert resp.headers["content-type"] == "application/problem+json"
