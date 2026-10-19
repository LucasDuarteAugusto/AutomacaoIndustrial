from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.rate_limit import LimitadorMemoria, resolver_regra
from app.main import create_app


async def test_limitador_memoria_bloqueia_apos_limite() -> None:
    limitador = LimitadorMemoria()
    for _ in range(3):
        ok, _ = await limitador.verificar("k", 3, 60)
        assert ok
    ok, retry = await limitador.verificar("k", 3, 60)
    assert not ok
    assert retry >= 1


def test_resolver_regra_exempta_health(settings: Settings) -> None:
    assert resolver_regra("/health", settings) is None
    assert resolver_regra("/ready", settings) is None
    auth = resolver_regra("/v1/auth/login", settings)
    assert auth is not None
    assert auth.prefixo_chave == "auth"
    troca_senha = resolver_regra("/v1/auth/me/senha", settings)
    assert troca_senha is not None
    assert troca_senha.prefixo_chave == "auth"
    me = resolver_regra("/v1/auth/me", settings)
    assert me is not None
    assert me.prefixo_chave == "api"


@pytest.fixture
async def cliente_com_rate_limit(settings: Settings) -> AsyncIterator[AsyncClient]:
    limitado = settings.model_copy(
        update={
            "rate_limit_habilitado": True,
            "rate_limit_auth_por_minuto": 2,
            "rate_limit_padrao_por_minuto": 2,
        }
    )
    app = create_app(limitado)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente,
    ):
        yield cliente


async def test_rate_limit_login_retorna_429(cliente_com_rate_limit: AsyncClient) -> None:
    payload = {"email": "a@example.com", "senha": "senha-forte"}
    assert (await cliente_com_rate_limit.post("/v1/auth/login", json=payload)).status_code != 429
    assert (await cliente_com_rate_limit.post("/v1/auth/login", json=payload)).status_code != 429
    resp = await cliente_com_rate_limit.post("/v1/auth/login", json=payload)
    assert resp.status_code == 429
    assert resp.headers["content-type"] == "application/problem+json"
    assert resp.headers.get("retry-after")
    assert resp.json()["title"] == "Limite de requisições excedido"


async def test_health_nao_sofre_rate_limit(cliente_com_rate_limit: AsyncClient) -> None:
    for _ in range(5):
        assert (await cliente_com_rate_limit.get("/health")).status_code == 200
