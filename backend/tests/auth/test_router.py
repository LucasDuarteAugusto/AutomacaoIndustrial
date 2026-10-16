from httpx import AsyncClient

from app.auth.models import Perfil


async def test_rota_protegida_sem_token_retorna_401(client_sem_auth: AsyncClient) -> None:
    resp = await client_sem_auth.get("/v1/fabricantes")
    assert resp.status_code == 401
    assert resp.headers["content-type"] == "application/problem+json"
    assert resp.json()["title"] == "Não autorizado"


async def test_bootstrap_cria_admin_e_retorna_token(client_sem_auth: AsyncClient) -> None:
    resp = await client_sem_auth.post(
        "/v1/auth/bootstrap",
        json={"email": "admin@example.com", "senha": "senha-forte", "nome": "Admin"},
    )
    assert resp.status_code == 201
    corpo = resp.json()
    assert corpo["token_type"] == "bearer"  # noqa: S105
    assert corpo["access_token"]
    assert corpo["usuario"]["perfil"] == Perfil.ADMIN
    assert corpo["usuario"]["email"] == "admin@example.com"


async def test_bootstrap_segunda_vez_retorna_409(client_sem_auth: AsyncClient) -> None:
    payload = {"email": "primeiro@example.com", "senha": "senha-forte", "nome": "Primeiro"}
    assert (await client_sem_auth.post("/v1/auth/bootstrap", json=payload)).status_code == 201
    resp = await client_sem_auth.post(
        "/v1/auth/bootstrap",
        json={"email": "outro@example.com", "senha": "senha-forte", "nome": "Outro"},
    )
    assert resp.status_code == 409


async def test_login_e_me(client_sem_auth: AsyncClient) -> None:
    await client_sem_auth.post(
        "/v1/auth/bootstrap",
        json={"email": "ops@example.com", "senha": "senha-forte", "nome": "Ops"},
    )
    login = await client_sem_auth.post(
        "/v1/auth/login",
        json={"email": "ops@example.com", "senha": "senha-forte"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = await client_sem_auth.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "ops@example.com"


async def test_login_senha_errada_retorna_401(client_sem_auth: AsyncClient) -> None:
    await client_sem_auth.post(
        "/v1/auth/bootstrap",
        json={"email": "user@example.com", "senha": "senha-forte", "nome": "User"},
    )
    resp = await client_sem_auth.post(
        "/v1/auth/login",
        json={"email": "user@example.com", "senha": "erradaaaaa"},
    )
    assert resp.status_code == 401


async def test_leitura_nao_pode_criar_fabricante(client_leitura: AsyncClient) -> None:
    resp = await client_leitura.post("/v1/fabricantes", json={"nome": "ABB"})
    assert resp.status_code == 403
    assert resp.json()["title"] == "Proibido"


async def test_admin_pode_criar_usuario(client: AsyncClient) -> None:
    resp = await client.post(
        "/v1/auth/usuarios",
        json={
            "email": "leitura@example.com",
            "senha": "senha-forte",
            "nome": "Leitura",
            "perfil": "LEITURA",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["perfil"] == "LEITURA"


async def test_cors_preflight_aceita_origem_configurada(client: AsyncClient) -> None:
    resp = await client.options(
        "/v1/fabricantes",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
