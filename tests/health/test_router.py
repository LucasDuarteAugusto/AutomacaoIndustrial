from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app


async def test_health_retorna_ok(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_ready_com_banco_disponivel_retorna_ok(client: AsyncClient) -> None:
    resp = await client.get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_ready_com_banco_indisponivel_retorna_503_problem_json() -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://ninguem:senha@127.0.0.1:1/inexistente",
        ambiente="teste",
    )
    app = create_app(settings)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente,
    ):
        resp = await cliente.get("/ready")

    assert resp.status_code == 503
    assert resp.headers["content-type"] == "application/problem+json"
    assert resp.json()["instance"] == "/ready"
