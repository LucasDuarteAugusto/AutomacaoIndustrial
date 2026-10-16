# 00 — Guia de teste manual (em casa)

Roteiro para validar o backend de ponta a ponta no Windows, sem frontend. Tempo estimado: 30–60 min (mais se for configurar Voyage/OpenAI).

## O que você precisa

| Item | Obrigatório? |
|---|---|
| Docker Desktop aberto | Sim |
| [uv](https://docs.astral.sh/uv/) | Sim |
| Conta [Voyage](https://www.voyageai.com/) (`VOYAGE_API_KEY`) | Só para ingestão/busca/agente **reais** |
| Conta [OpenAI](https://platform.openai.com/) (`OPENAI_API_KEY`) | Só para o agente Q&A |
| Um PDF técnico pequeno (manual, 5–20 páginas) | Recomendado |

Sem chaves de IA você ainda valida: health, auth, catálogo, parâmetros/falhas e upload (o status do documento pode ficar `PENDENTE`/`ERRO` sem Voyage).

## 1. Subir o ambiente

Na **raiz** do repositório:

```powershell
Copy-Item .env.example .env
# Só o Postgres — a API roda com uv (evita conflito na porta 8000)
docker compose up -d db --wait
```

Em **`backend/`**:

```powershell
Copy-Item .env.example .env
# Se for testar ingestão/agente, edite .env e preencha:
#   VOYAGE_API_KEY=...
#   OPENAI_API_KEY=...

uv sync
uv run alembic upgrade head
uv run uvicorn app.main:create_app --factory --reload
```

Confira:

| URL | Esperado |
|---|---|
| <http://127.0.0.1:8000/health> | `{"status":"ok"}` |
| <http://127.0.0.1:8000/ready> | `{"status":"ok"}` |
| <http://127.0.0.1:8000/docs> | Swagger |

Detalhes e troubleshooting: [01 — Rodando localmente](01-rodando-localmente.md).

### Modo só Docker (alternativa)

```powershell
# Na raiz — sobe Postgres + API na imagem
docker compose up -d --build --wait
```

Nesse modo **não** rode o uvicorn local (a porta 8000 já está ocupada). Migrations rodam no start do container.

## 2. Autenticar (obrigatório para `/v1`)

No Swagger: **Authorize** → cole `Bearer <token>` (ou só o token, conforme a UI pedir).

### Bootstrap (primeira vez — base sem usuários)

```http
POST /v1/auth/bootstrap
Content-Type: application/json

{
  "email": "admin@example.com",
  "senha": "senha-forte-123",
  "nome": "Admin Local"
}
```

Guarde `access_token`. Se retornar **409**, já existe usuário — use login.

### Login

```http
POST /v1/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "senha": "senha-forte-123"
}
```

### Conferir

```http
GET /v1/auth/me
Authorization: Bearer <access_token>
```

Docs: [13 — Auth](13-auth.md).

## 3. Catálogo mínimo

Com o token no Authorize:

1. `GET /v1/tipos-equipamento` → anote um `id_tipo_equipamento` (ex.: `INVERSOR`).
2. `POST /v1/fabricantes` → `{ "nome": "Siemens Teste" }` → anote `id_fabricante`.
3. `POST /v1/familias` → `id_fabricante`, `id_tipo_equipamento`, `nome` (ex.: `SINAMICS G120 Teste`) → anote `id_familia`.
4. (Opcional) `POST /v1/equipamentos` ligado à família.

## 4. Documento + PDF

```http
POST /v1/documentos
{
  "titulo": "Manual teste rampa",
  "tipo_documento": "LISTA_PARAMETROS",
  "idioma": "pt-BR",
  "ids_familias": ["<id_familia>"]
}
```

Anexe o arquivo:

```http
POST /v1/documentos/{id_documento}/arquivo
Content-Type: multipart/form-data
arquivo: <seu.pdf>
```

Acompanhe `GET /v1/documentos/{id}`:

| `status_processamento` | Significado |
|---|---|
| `PENDENTE` / `PROCESSANDO` | Aguardando / em andamento |
| `INDEXADO` | Pronto para busca (precisa `VOYAGE_API_KEY` válida) |
| `ERRO` | Veja `erro_processamento` (chave ausente, PDF inválido, etc.) |

Docs: [10 — Armazenamento](10-armazenamento.md), [11 — Ingestão](11-ingestao.md).

## 5. Parâmetro e falha estruturados

Útil mesmo sem PDF — o agente usa esses registros quando a pergunta cita códigos.

```http
POST /v1/parametros
{
  "id_familia": "<id_familia>",
  "codigo": "p1120",
  "nome": "Tempo de rampa",
  "descricao": "Tempo de rampa de aceleração",
  "unidade": "s",
  "valor_min": 0,
  "valor_max": 999,
  "valor_padrao": "10"
}

POST /v1/falhas
{
  "id_familia": "<id_familia>",
  "codigo": "F07801",
  "tipo": "FALHA",
  "titulo": "Sobrecorrente",
  "causa": "Carga excessiva ou curto",
  "solucao": "Verificar motor e cabo"
}
```

Docs: [15 — Parâmetros e falhas](15-parametros-falhas.md).

## 6. Busca híbrida (precisa documento INDEXADO + Voyage)

```http
POST /v1/busca
{
  "consulta": "tempo de rampa p1120",
  "limit": 5,
  "id_familia": "<id_familia>"
}
```

Espere `items` com `conteudo`, `pagina`, `score`. Sem trechos indexados, `items` vem vazio.

Docs: [12 — Busca](12-busca.md).

## 7. Agente Q&A (precisa OpenAI; Voyage se usar trechos)

```http
POST /v1/agente/perguntar
{
  "pergunta": "O que significa o parâmetro p1120?",
  "id_familia": "<id_familia>",
  "limit": 5
}
```

Espere:

- `resposta` em português
- `parametros` com o hit de `p1120` (mesmo sem PDF)
- `citacoes` se houver trechos da busca
- `modelo_llm` (ex.: `gpt-5-mini`)

Teste também: `"pergunta": "O que é F07801?"`.

Docs: [14 — Agente](14-agente.md).

## 8. Checklist rápido

| # | Cenário | OK? |
|---|---|---|
| 1 | `/health` e `/ready` | |
| 2 | Bootstrap ou login + `/me` | |
| 3 | Criar fabricante / família | |
| 4 | Criar documento + upload PDF | |
| 5 | Status `INDEXADO` (com Voyage) | |
| 6 | CRUD parâmetro / falha | |
| 7 | `POST /v1/busca` retorna trechos | |
| 8 | `POST /v1/agente/perguntar` cita fontes | |
| 9 | Sem token → 401 em `/v1/fabricantes` | |
| 10 | `uv run pytest` na pasta `backend/` (Docker aberto) | |

## 9. Testes automatizados

```powershell
cd backend
uv run pytest -q
```

Precisa do Docker Desktop (testcontainers sobe `pgvector/pgvector:pg17`). Ver [06 — Testes](06-testes.md).

## 10. Opcional: API só em Docker / escala

| Objetivo | Comando (raiz) |
|---|---|
| db + api (imagem) | `docker compose up -d --build --wait` |
| Produção local | ver [17 — Deploy](17-deploy.md) |
| 3 réplicas + nginx | ver [19 — Escala](19-escala.md) |
| + Redis | ver [20 — Redis](20-redis.md) |

## Problemas comuns neste roteiro

| Sintoma | O que fazer |
|---|---|
| Porta 8000 em uso | `docker compose stop api` ou use só `db` + uvicorn |
| 401 em tudo | Authorize no Swagger / rode bootstrap |
| Upload OK mas nunca `INDEXADO` | Preencha `VOYAGE_API_KEY` e veja logs / `erro_processamento` |
| Agente 503 | Preencha `OPENAI_API_KEY` |
| 429 | Rate limit; aguarde 1 min ou suba `RATE_LIMIT_*` no `.env` |

Índice geral: [README](../README.md).
