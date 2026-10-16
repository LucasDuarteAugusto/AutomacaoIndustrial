# 20 — Redis (rate limit compartilhado)

Com várias réplicas da API, o contador em memória diverge. O Redis centraliza a janela deslizante.

## Compose

```powershell
docker compose `
  -f docker-compose.yml `
  -f docker-compose.scale.yml `
  -f docker-compose.redis.yml `
  up -d --build --scale api=3
```

Variáveis injetadas em `api`:

| Variável | Valor |
|---|---|
| `RATE_LIMIT_BACKEND` | `redis` |
| `REDIS_URL` | `redis://redis:6379/0` |

## Código

`LimitadorRedis` em `app/core/rate_limit.py` (sorted set + TTL). Sem Redis, use `RATE_LIMIT_BACKEND=memoria` (padrão).

## Além do rate limit

O mesmo Redis pode servir depois para cache de busca, filas de ingestão e pub/sub — fora do escopo desta entrega.

## Ordem prática concluída

1. Deploy estável  
2. Rate limiting  
3. Réplicas + LB  
4. Redis compartilhado  

Próximo foco de produto: clientes React/Android, ou extração assistida / histórico do agente.
