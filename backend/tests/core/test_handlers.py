from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.errors import Conflito, NaoEncontrado
from app.main import create_app


@pytest.fixture
async def cliente_com_rotas_de_erro(settings: Settings) -> AsyncIterator[AsyncClient]:
    app: FastAPI = create_app(settings)

    @app.get("/_teste/nao-encontrado")
    async def _nao_encontrado() -> None:
        raise NaoEncontrado("Documento 123 não existe.")

    @app.get("/_teste/conflito")
    async def _conflito() -> None:
        raise Conflito("Já existe um documento com esse código.")

    @app.get("/_teste/validacao")
    async def _validacao(potencia_kw: float) -> float:
        return potencia_kw

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente:
        yield cliente


async def test_rota_inexistente_retorna_404_problem_json(client: AsyncClient) -> None:
    resp = await client.get("/nao-existe")
    assert resp.status_code == 404
    assert resp.headers["content-type"] == "application/problem+json"
    assert resp.json()["title"] == "Not Found"


async def test_nao_encontrado_vira_404_problem_json(cliente_com_rotas_de_erro: AsyncClient) -> None:
    resp = await cliente_com_rotas_de_erro.get("/_teste/nao-encontrado")
    assert resp.status_code == 404
    assert resp.headers["content-type"] == "application/problem+json"
    assert resp.json() == {
        "type": "about:blank",
        "title": "Recurso não encontrado",
        "status": 404,
        "detail": "Documento 123 não existe.",
        "instance": "/_teste/nao-encontrado",
    }


async def test_conflito_vira_409_problem_json(cliente_com_rotas_de_erro: AsyncClient) -> None:
    resp = await cliente_com_rotas_de_erro.get("/_teste/conflito")
    assert resp.status_code == 409
    assert resp.headers["content-type"] == "application/problem+json"


async def test_parametro_invalido_retorna_422_com_lista_de_erros(cliente_com_rotas_de_erro: AsyncClient) -> None:
    resp = await cliente_com_rotas_de_erro.get("/_teste/validacao", params={"potencia_kw": "abc"})
    assert resp.status_code == 422
    assert resp.headers["content-type"] == "application/problem+json"
    assert resp.json()["errors"][0]["loc"] == ["query", "potencia_kw"]
