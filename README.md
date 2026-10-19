# AutomacaoIndustrial

Plataforma de apoio a profissionais de automação industrial no **comissionamento de acionamentos de motores**: relés de gerenciamento (SIMOCODE), soft starters e inversores de frequência.

O backend organiza a documentação técnica dos fabricantes (fabricantes → famílias → modelos → documentos), indexa PDFs com **busca semântica (pgvector)** e expõe um **agente Q&A** com citação de fontes, autenticação JWT e dados estruturados de parâmetros/falhas. O frontend React oferece o assistente, a busca e a gestão de documentos.

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.143-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17%20%2B%20pgvector-4169E1?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.1%20async-D71F00)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-24%20LTS-5FA04E?logo=nodedotjs&logoColor=white)

## Início rápido

Pré-requisitos: [uv](https://docs.astral.sh/uv/) e Docker Desktop.

```powershell
# Banco apenas (na raiz) — a API sobe com uv para hot reload
Copy-Item .env.example .env
docker compose up -d db --wait

# API (em backend/)
cd backend
Copy-Item .env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:create_app --factory --reload
```

Documentação interativa da API: <http://127.0.0.1:8000/docs>

```powershell
# Frontend (em frontend/) — Node 24 + pnpm 11; a API precisa estar no ar
corepack enable pnpm
pnpm install
pnpm dev    # http://localhost:5173
```

Detalhes do frontend: [22 — Frontend](docs/22-frontend.md).

**Testar em casa (roteiro completo):** [00 — Guia de teste manual](docs/00-guia-teste-manual.md).  
Passo a passo e troubleshooting: [01 — Rodando localmente](docs/01-rodando-localmente.md).

## Documentação

| Documento | Conteúdo |
|---|---|
| [00 — Guia de teste manual](docs/00-guia-teste-manual.md) | Roteiro ponta a ponta para validar o backend em casa (Swagger) |
| [01 — Rodando localmente](docs/01-rodando-localmente.md) | Pré-requisitos, primeira execução, variáveis de ambiente, comandos do dia a dia e solução de problemas |
| [02 — Banco de dados](docs/02-banco-de-dados.md) | Diagrama, tabelas, colunas, restrições e convenções de nomes |
| [03 — Migrations](docs/03-migrations.md) | Como criar, revisar, aplicar e desfazer mudanças no schema com Alembic |
| [04 — Arquitetura](docs/04-arquitetura.md) | Stack, monorepo, camadas, estrutura de pastas e decisões técnicas |
| [05 — API](docs/05-api.md) | Rotas, paginação, filtros, formato de erros e exemplos |
| [06 — Testes](docs/06-testes.md) | Como os testes funcionam, como rodar e como escrever novos |
| [07 — Domínio de acionamentos](docs/07-dominio-acionamentos.md) | Glossário técnico (SIMOCODE, soft starter, inversor) e como isso vira dado |
| [08 — Roadmap](docs/08-roadmap.md) | Fases do projeto e próximos passos |
| [09 — Estudo de modelos de IA](docs/09-estudo-modelos-ia.md) | Custo-benefício de modelos de embedding e LLM para a busca semântica e o agente |
| [10 — Armazenamento](docs/10-armazenamento.md) | PDFs em disco (local) ou S3-compatível (Cloudflare R2 / AWS S3) |
| [11 — Ingestão](docs/11-ingestao.md) | Pipeline PDF → trechos → embeddings Voyage → `TRECHOS` |
| [12 — Busca](docs/12-busca.md) | Busca híbrida `POST /v1/busca` (vetor + textual + RRF) |
| [13 — Auth](docs/13-auth.md) | JWT (perfis ADMIN/OPERADOR/LEITURA) e CORS |
| [14 — Agente](docs/14-agente.md) | Q&A com busca híbrida, LLM e citações |
| [15 — Parâmetros e falhas](docs/15-parametros-falhas.md) | Tabelas estruturadas + lookup no agente |
| [16 — Docker e CI](docs/16-docker-ci.md) | Imagem da API, Compose e GitHub Actions |
| [17 — Deploy](docs/17-deploy.md) | Compose prod, secrets, GHCR |
| [18 — Rate limit](docs/18-rate-limit.md) | Limites por IP (memória; Redis depois) |
| [19 — Escala](docs/19-escala.md) | Réplicas da API + nginx (load balancer) |
| [20 — Redis](docs/20-redis.md) | Rate limit compartilhado entre réplicas |
| [21 — Estudo do frontend React](docs/21-estudo-frontend-react.md) | Stack e versões, arquitetura SPA, integração com a API, telas, lacunas do backend e plano de entrega |
| [22 — Frontend](docs/22-frontend.md) | Como rodar, contrato OpenAPI → Orval, sessão, telas, testes e imagem de produção |

## Estrutura do repositório

```text
AutomacaoIndustrial/
├── backend/             API FastAPI (Python 3.14, SQLAlchemy async, Alembic)
│   ├── app/             código: core/, auth/, catalogo/, documentos/, parametros/, falhas/, busca/, agente/, health/
│   ├── Dockerfile       imagem de produção/local via Compose
│   ├── migrations/      versões do schema
│   └── tests/           testes contra PostgreSQL real (testcontainers)
├── frontend/            SPA React 19 + Vite 8 + TypeScript 6 (pnpm, Node 24)
│   ├── src/             rotas, features, componentes, cliente gerado do OpenAPI
│   ├── openapi.json     contrato exportado do backend (versionado)
│   └── Dockerfile       nginx com o build + proxy de /v1 para a API
├── docs/                documentação
├── docker-compose.yml   PostgreSQL 17 + pgvector (+ serviço api)
├── docker-compose.prod.yml  override para deploy estável (+ serviço web)
├── .github/workflows/   CI + CD (GHCR)
└── .cursor/             regras e automações do assistente de IA
```

O repositório é um monorepo: `frontend/` e, depois, o aplicativo Android ficam ao lado de `backend/`, consumindo o contrato OpenAPI da API.

## Status

| Fase | Situação |
|---|---|
| Fundação (API, banco, migrations, testes) | Concluída |
| Catálogo de equipamentos e documentos | Concluída |
| Ingestão de PDFs e busca semântica | Concluída |
| Autenticação JWT + CORS | Concluída |
| Agente Q&A com citações | Concluída |
| Dados estruturados (parâmetros e falhas) | Concluída |
| Docker + CI (ruff, mypy, pytest) | Concluída |
| Deploy estável (Compose prod + GHCR) | Concluída |
| Rate limiting + escala + Redis | Concluída |
| Frontend: fundação, assistente, busca e documentos | Concluída |
| Frontend: catálogo, parâmetros, falhas e usuários | Planejada |
| Aplicativo Android | Planejada |

Detalhes em [Roadmap](docs/08-roadmap.md).
