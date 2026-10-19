from uuid import uuid4

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


async def _criar_usuario(client: AsyncClient, email: str, perfil: str = "OPERADOR", nome: str = "Usuário") -> str:
    resp = await client.post(
        "/v1/auth/usuarios",
        json={"email": email, "senha": "senha-forte", "nome": nome, "perfil": perfil},
    )
    assert resp.status_code == 201, resp.text
    id_usuario: str = resp.json()["id_usuario"]
    return id_usuario


async def test_listar_usuarios_paginado_e_filtrado(client: AsyncClient) -> None:
    await _criar_usuario(client, "ana@example.com", "ADMIN", "Ana")
    await _criar_usuario(client, "bruno@example.com", "OPERADOR", "Bruno")
    await _criar_usuario(client, "carla@example.com", "LEITURA", "Carla")

    todos = (await client.get("/v1/auth/usuarios", params={"limit": 2})).json()
    assert todos["total"] == 3
    assert [u["nome"] for u in todos["items"]] == ["Ana", "Bruno"]
    assert "senha_hash" not in todos["items"][0]

    por_perfil = (await client.get("/v1/auth/usuarios", params={"perfil": "LEITURA"})).json()
    assert [u["email"] for u in por_perfil["items"]] == ["carla@example.com"]

    por_busca = (await client.get("/v1/auth/usuarios", params={"busca": "BRUNO@"})).json()
    assert [u["nome"] for u in por_busca["items"]] == ["Bruno"]


async def test_listar_usuarios_filtra_por_ativo(client: AsyncClient) -> None:
    id_inativo = await _criar_usuario(client, "inativo@example.com")
    await _criar_usuario(client, "ativo@example.com")
    await client.patch(f"/v1/auth/usuarios/{id_inativo}", json={"ativo": False})

    resp = await client.get("/v1/auth/usuarios", params={"ativo": "false"})
    assert [u["email"] for u in resp.json()["items"]] == ["inativo@example.com"]


async def test_obter_usuario(client: AsyncClient) -> None:
    id_usuario = await _criar_usuario(client, "detalhe@example.com")
    resp = await client.get(f"/v1/auth/usuarios/{id_usuario}")
    assert resp.status_code == 200
    assert resp.json()["email"] == "detalhe@example.com"


async def test_obter_usuario_inexistente_retorna_404(client: AsyncClient) -> None:
    resp = await client.get(f"/v1/auth/usuarios/{uuid4()}")
    assert resp.status_code == 404
    assert resp.headers["content-type"] == "application/problem+json"


async def test_leitura_nao_lista_usuarios(client_leitura: AsyncClient) -> None:
    assert (await client_leitura.get("/v1/auth/usuarios")).status_code == 403
    assert (await client_leitura.get(f"/v1/auth/usuarios/{uuid4()}")).status_code == 403


async def test_rebaixar_ultimo_admin_retorna_409(client: AsyncClient) -> None:
    id_admin = await _criar_usuario(client, "unico-admin@example.com", "ADMIN")
    resp = await client.patch(f"/v1/auth/usuarios/{id_admin}", json={"perfil": "OPERADOR"})
    assert resp.status_code == 409
    assert resp.headers["content-type"] == "application/problem+json"


async def test_desativar_ultimo_admin_retorna_409(client: AsyncClient) -> None:
    id_admin = await _criar_usuario(client, "unico-admin@example.com", "ADMIN")
    resp = await client.patch(f"/v1/auth/usuarios/{id_admin}", json={"ativo": False})
    assert resp.status_code == 409


async def test_rebaixar_admin_com_outro_admin_ativo(client: AsyncClient) -> None:
    id_admin = await _criar_usuario(client, "admin-1@example.com", "ADMIN")
    await _criar_usuario(client, "admin-2@example.com", "ADMIN")
    resp = await client.patch(f"/v1/auth/usuarios/{id_admin}", json={"perfil": "OPERADOR"})
    assert resp.status_code == 200
    assert resp.json()["perfil"] == "OPERADOR"


async def test_alterar_nome_do_ultimo_admin_e_permitido(client: AsyncClient) -> None:
    id_admin = await _criar_usuario(client, "unico-admin@example.com", "ADMIN")
    resp = await client.patch(f"/v1/auth/usuarios/{id_admin}", json={"nome": "Novo nome", "perfil": "ADMIN"})
    assert resp.status_code == 200
    assert resp.json()["nome"] == "Novo nome"


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
