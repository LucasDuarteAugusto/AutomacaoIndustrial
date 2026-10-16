# 08 — Roadmap

## Concluído

| Fase | Entrega | Branch |
|---|---|---|
| 0 — Fundação | Projeto uv, FastAPI, configuração, logs, erros problem+json, Postgres+pgvector no Docker, Alembic, `/health`, `/ready`, testes com testcontainers | `feat/esqueleto-inicial` |
| 1 — Catálogo | Tipos de equipamento, fabricantes, famílias, equipamentos e documentos (metadados e vínculos N:N), com CRUD, filtros e paginação | `feat/catalogo` |
| — Monorepo | Projeto Python movido para `backend/`; `docker-compose.yml`, `docs/` e configurações compartilhadas na raiz; README na raiz | `feat/catalogo` |

## Próximas fases

### 2 — Ingestão e busca semântica

- [x] **Estudo e decisão inicial de modelos**: ver [09 — Estudo de modelos de IA](09-estudo-modelos-ia.md).
  - Embedding: Voyage `voyage-context-4` → `vector(1024)` (200M tokens grátis).
  - LLM (fase 4): GPT-5 mini; modelos mais fortes sob demanda.
  - Reserva: Perplexity (texto) ou Gemini Embedding 2 (multimodal), se o teste com manuais reais pedir.
- [x] Núcleo IA + `TRECHOS` (branch `feat/ingestao-busca`): Settings (Voyage/OpenAI), `ProvedorEmbedding` / `ProvedorLLM`, tabela `TRECHOS` com `vector(1024)`, HNSW e `tsvector`.
- [x] Armazenamento de arquivos (`feat/armazenamento-local`): `ArmazenamentoLocal` padrão; adaptador S3-compatível pronto para Cloudflare R2 (e AWS S3 depois).
- [x] Upload de PDF (`feat/upload-documento`): `POST /v1/documentos/{id}/arquivo` → hash, chave, tamanho; deduplicação por SHA-256; troca de arquivo limpa trechos.
- [x] Pipeline de ingestão (`feat/pipeline-ingestao`): PyMuPDF → chunking → Voyage → `TRECHOS`; `POST .../reprocessar`; ver [11 — Ingestão](11-ingestao.md).
- [x] Busca híbrida (`feat/busca-hibrida`): `POST /v1/busca` (vetor + `tsvector` + RRF + filtros); ver [12 — Busca](12-busca.md).
- [ ] Validar recall@5 com 30 a 50 perguntas reais sobre 2 ou 3 manuais (antes de fechar o modelo em produção).
- [ ] Descrição de figuras (diagramas, telas de IHM) por LLM com visão, indexada como trecho de texto.

### 3 — Dados estruturados

- [ ] Tabela `PARAMETROS` (código, descrição, unidade, faixa, valor padrão, por família e firmware).
- [ ] Tabela `FALHAS` (código, tipo falha/alarme, causa, solução).
- [ ] Extração assistida a partir das listas de parâmetros e de falhas.

### 4 — Agente de IA

- [ ] Endpoint de pergunta e resposta com citação das fontes (documento, página, seção).
- [ ] Ferramentas do agente: busca híbrida, consulta de parâmetro, consulta de falha.
- [ ] Histórico de conversas por usuário.

### 5 — Produção e clientes

- [x] Autenticação JWT (pyjwt + pwdlib/argon2) e perfis (`feat/auth-jwt-cors`); ver [13 — Auth](13-auth.md).
- [x] CORS para o frontend React.
- [ ] `Dockerfile` da API e pipeline de CI (ruff, mypy, pytest).
- [ ] Deploy (banco gerenciado com pgvector + container da API).
- [ ] Frontend React e aplicativo Android consumindo o OpenAPI.
