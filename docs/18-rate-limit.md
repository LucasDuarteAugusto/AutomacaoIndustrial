# 18 — Rate limiting

Protege a API contra abuso e picos (login, busca e agente) **antes** de escalar com várias réplicas.

## Comportamento

Middleware por IP (`X-Forwarded-For` ou peer). Resposta **429** em `application/problem+json` com header `Retry-After`.

| Prefixo | Limite padrão (por minuto) | Env |
|---|---|---|
| `/v1/auth/login`, `/bootstrap` | 20 | `RATE_LIMIT_AUTH_POR_MINUTO` |
| `/v1/busca` | 60 | `RATE_LIMIT_BUSCA_POR_MINUTO` |
| `/v1/agente` | 20 | `RATE_LIMIT_AGENTE_POR_MINUTO` |
| demais `/v1/*` | 120 | `RATE_LIMIT_PADRAO_POR_MINUTO` |
| `/health`, `/ready`, OpenAPI | isento | — |

Desligar: `RATE_LIMIT_HABILITADO=false` (nos testes automáticos já vem desligado).

Backend atual: **`memoria`** (por processo). Com várias réplicas o contador não é compartilhado — a etapa Redis resolve isso (`RATE_LIMIT_BACKEND=redis`).

## Código

`app/core/rate_limit.py` — `Limitador` (protocolo), `LimitadorMemoria`, `RateLimitMiddleware`.

## Próximo passo

Escala: [19 — Réplicas e LB](19-escala.md). Redis para contadores compartilhados entre réplicas.
