# 18 — Rate limiting

Protege a API contra abuso e picos (login, busca e agente) **antes** de escalar com várias réplicas.

## Comportamento

Middleware com janela deslizante de 1 minuto. Resposta **429** em `application/problem+json` com header `Retry-After`.

### Quem é contado

| Situação | Chave do contador |
|---|---|
| `Authorization: Bearer <token>` com JWT válido | Usuário (`sub` do token) |
| Sem token, token inválido ou expirado | IP (`X-Forwarded-For` ou peer) |
| Rotas de autenticação (login, bootstrap, troca de senha) | Sempre IP, mesmo com token (contra força bruta) |

Contar por usuário evita que vários técnicos atrás do mesmo NAT da fábrica dividam um único limite. O token é só decodificado (assinatura e expiração), sem consulta ao banco; o 401 de usuário inexistente ou inativo continua vindo da rota. Para voltar ao comportamento só por IP: `RATE_LIMIT_POR_USUARIO=false`.

### Limites

| Prefixo | Limite padrão (por minuto) | Env |
|---|---|---|
| `/v1/auth/login`, `/bootstrap`, `/me/senha` | 20 | `RATE_LIMIT_AUTH_POR_MINUTO` |
| `/v1/busca` | 60 | `RATE_LIMIT_BUSCA_POR_MINUTO` |
| `/v1/agente` | 20 | `RATE_LIMIT_AGENTE_POR_MINUTO` |
| demais `/v1/*` | 120 | `RATE_LIMIT_PADRAO_POR_MINUTO` |
| `/health`, `/ready`, OpenAPI | isento | — |

Desligar: `RATE_LIMIT_HABILITADO=false` (nos testes automáticos já vem desligado).

Backend: **`memoria`** (padrão) ou **`redis`** (`RATE_LIMIT_BACKEND=redis` + `REDIS_URL`). Com réplicas, use Redis — ver [20](20-redis.md).

## Código

`app/core/rate_limit.py` — `Limitador` (protocolo), `LimitadorMemoria`, `LimitadorRedis`, `RateLimitMiddleware`, `chave_por_usuario_ou_ip`.

## Próximo passo

Escala: [19 — Réplicas e LB](19-escala.md). Redis para contadores compartilhados entre réplicas.
