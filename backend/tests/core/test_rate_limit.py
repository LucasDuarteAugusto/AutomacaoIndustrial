from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request

from app.auth.models import Perfil
from app.auth.seguranca import criar_access_token
from app.core.config import Settings
from app.core.rate_limit import LimitadorMemoria, chave_por_usuario_ou_ip, resolver_regra
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


def _bearer(settings: Settings) -> dict[str, str]:
    token = criar_access_token(settings=settings, id_usuario=uuid4(), email="x@example.com", perfil=Perfil.OPERADOR)
    return {"Authorization": f"Bearer {token}"}


def _requisicao(path: str, headers: dict[str, str] | None = None, ip: str = "10.0.0.1") -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "scheme": "http",
            "server": ("test", 80),
            "path": path,
            "query_string": b"",
            "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
            "client": (ip, 12345),
        }
    )


def test_chave_usa_sub_do_token_valido(settings: Settings) -> None:
    token = criar_access_token(settings=settings, id_usuario=UUID(int=7), email="x@example.com", perfil=Perfil.LEITURA)
    chave = chave_por_usuario_ou_ip(settings)
    assert chave(_requisicao("/v1/fabricantes", {"Authorization": f"Bearer {token}"})) == f"u:{UUID(int=7)}"


def test_chave_sem_token_ou_token_invalido_usa_ip(settings: Settings) -> None:
    chave = chave_por_usuario_ou_ip(settings)
    assert chave(_requisicao("/v1/fabricantes")) == "ip:10.0.0.1"
    assert chave(_requisicao("/v1/fabricantes", {"Authorization": "Bearer invalido"})) == "ip:10.0.0.1"
    assert chave(_requisicao("/v1/fabricantes", {"Authorization": "Basic abc"})) == "ip:10.0.0.1"


def test_chave_de_rotas_de_auth_sempre_por_ip(settings: Settings) -> None:
    chave = chave_por_usuario_ou_ip(settings)
    for path in ("/v1/auth/login", "/v1/auth/bootstrap", "/v1/auth/me/senha"):
        assert chave(_requisicao(path, _bearer(settings), ip="10.0.0.9")) == "ip:10.0.0.9"


def test_chave_por_usuario_desligada_usa_ip(settings: Settings) -> None:
    desligado = settings.model_copy(update={"rate_limit_por_usuario": False})
    chave = chave_por_usuario_ou_ip(desligado)
    assert chave(_requisicao("/v1/fabricantes", _bearer(desligado))) == "ip:10.0.0.1"


async def test_tokens_diferentes_no_mesmo_ip_tem_limites_independentes(
    cliente_com_rate_limit: AsyncClient, settings: Settings
) -> None:
    usuario_a, usuario_b = _bearer(settings), _bearer(settings)
    for _ in range(2):
        assert (await cliente_com_rate_limit.get("/v1/fabricantes", headers=usuario_a)).status_code != 429
    assert (await cliente_com_rate_limit.get("/v1/fabricantes", headers=usuario_a)).status_code == 429
    assert (await cliente_com_rate_limit.get("/v1/fabricantes", headers=usuario_b)).status_code != 429
    assert (await cliente_com_rate_limit.get("/v1/fabricantes")).status_code != 429


async def test_requisicoes_sem_token_compartilham_limite_do_ip(cliente_com_rate_limit: AsyncClient) -> None:
    assert (await cliente_com_rate_limit.get("/v1/fabricantes")).status_code != 429
    invalido = {"Authorization": "Bearer invalido"}
    assert (await cliente_com_rate_limit.get("/v1/fabricantes", headers=invalido)).status_code != 429
    assert (await cliente_com_rate_limit.get("/v1/fabricantes")).status_code == 429


async def test_health_nao_sofre_rate_limit(cliente_com_rate_limit: AsyncClient) -> None:
    for _ in range(5):
        assert (await cliente_com_rate_limit.get("/health")).status_code == 200
