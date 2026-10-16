# 19 — Réplicas e load balancer

Distribui carga entre várias instâncias da API. O JWT continua stateless — qualquer réplica valida o token.

## Compose com escala

Arquivos: `docker-compose.scale.yml` + `deploy/nginx.conf`.

```powershell
# 3 réplicas da API + nginx na porta 8000
docker compose -f docker-compose.yml -f docker-compose.scale.yml up -d --build --scale api=3
```

Fluxo:

```text
cliente → nginx (:8000) → DNS round-robin → api:8000 (réplica 1..N)
                              ↘ Postgres (db)
```

O proxy envia `X-Forwarded-For` para o rate limit enxergar o IP real do cliente.

## Produção + escala

Combine com o override de produção:

```powershell
docker compose `
  -f docker-compose.yml `
  -f docker-compose.prod.yml `
  -f docker-compose.scale.yml `
  --env-file .env.production `
  up -d --scale api=3
```

## Limitações

- Rate limit **em memória** conta por réplica (3× o limite efetivo). Próxima etapa: **Redis**.
- Uploads grandes: `client_max_body_size 60m` no nginx (alinhado ao limite de PDF).
- Sem sticky session (não é necessário com JWT).

## Próximo passo

Redis: [20 — Redis](20-redis.md) (`docker-compose.redis.yml`).
