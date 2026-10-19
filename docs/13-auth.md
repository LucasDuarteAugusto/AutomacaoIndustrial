# 13 — Autenticação JWT e CORS

A API exige `Authorization: Bearer <token>` em todas as rotas `/v1/...`, exceto login e bootstrap (status e criação). Health (`/health`, `/ready`) permanece público.

## Fluxo inicial

1. `GET /v1/auth/bootstrap` responde `{"necessario": true}` enquanto a tabela `USUARIOS` estiver vazia (o frontend usa para decidir se mostra a tela de primeiro acesso).
2. Com a base vazia, chame `POST /v1/auth/bootstrap` (cria o primeiro `ADMIN` e devolve o token).
3. Depois use `POST /v1/auth/login` com e-mail e senha.
4. Envie o header em demais chamadas: `Authorization: Bearer <access_token>`.

No Swagger: **Authorize** após o bootstrap/login. Bootstrap retorna **409** se já existir qualquer usuário.

Exemplo rápido (PowerShell / após a API no ar):

```powershell
# Bootstrap (só na primeira vez)
Invoke-RestMethod http://127.0.0.1:8000/v1/auth/bootstrap -Method Post -ContentType application/json -Body '{"email":"admin@example.com","senha":"senha-forte-123","nome":"Admin"}'
```

## Perfis

| Perfil | Leitura (`GET` / busca) | Escrita (POST/PATCH/DELETE / upload) | Gestão de usuários |
|---|---|---|---|
| `ADMIN` | sim | sim | sim (`/v1/auth/usuarios`) |
| `OPERADOR` | sim | sim | não |
| `LEITURA` | sim | não (403) | não |

## Rotas

| Método | Rota | Auth |
|---|---|---|
| `GET` | `/v1/auth/bootstrap` | público — `{"necessario": bool}` |
| `POST` | `/v1/auth/bootstrap` | público (só se não houver usuários) |
| `POST` | `/v1/auth/login` | público |
| `GET` | `/v1/auth/me` | Bearer |
| `POST` | `/v1/auth/me/senha` | Bearer (qualquer perfil) — troca a própria senha, 204 |
| `GET` | `/v1/auth/usuarios` | Bearer + `ADMIN` — paginado; filtros `busca` (nome/e-mail), `perfil`, `ativo` |
| `GET` | `/v1/auth/usuarios/{id}` | Bearer + `ADMIN` |
| `POST` | `/v1/auth/usuarios` | Bearer + `ADMIN` |
| `PATCH` | `/v1/auth/usuarios/{id}` | Bearer + `ADMIN` |

### Regras

- **Último ADMIN:** rebaixar ou desativar o único `ADMIN` ativo retorna **409**. Promova outro usuário antes.
- **Troca de senha:** corpo `{"senha_atual": "...", "senha_nova": "..."}` (nova com 8 a 128 caracteres). Senha atual errada ou nova igual à atual retornam **422** (não 401, para o cliente não encerrar a sessão). A rota fica no limite de requisições de autenticação ([18](18-rate-limit.md)).

Resposta de login/bootstrap:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "expires_in": 28800,
  "usuario": { "id_usuario": "...", "email": "...", "nome": "...", "perfil": "ADMIN", "ativo": true, ... }
}
```

## CORS

Origens permitidas vêm de `CORS_ORIGINS` (lista separada por vírgula). Padrão local: `http://localhost:5173,http://localhost:3000`. Credenciais habilitadas (`allow_credentials=True`).

## Variáveis

| Variável | Padrão | Uso |
|---|---|---|
| `JWT_SECRET` | valor de desenvolvimento | Assinatura HS256 — **trocar em produção** |
| `JWT_ALGORITHM` | `HS256` | Algoritmo JWT |
| `JWT_EXPIRACAO_MINUTOS` | `480` (8 h) | Validade do access token |
| `CORS_ORIGINS` | frontends locais | Origens permitidas |

## Código

`app/auth/` — models (`USUARIOS`), seguranca (Argon2 + JWT), service, deps (`exigir_usuario`, `exigir_operacao_escrita`, `exigir_admin`), router.

Nos testes, `conftest` sobrescreve `get_usuario_atual` com um ADMIN sintético; use `client_sem_auth` / `client_leitura` quando precisar do fluxo real ou do perfil LEITURA.

## Próximo passo

Teste ponta a ponta: [00 — Guia de teste manual](00-guia-teste-manual.md). Agente: [14](14-agente.md).
