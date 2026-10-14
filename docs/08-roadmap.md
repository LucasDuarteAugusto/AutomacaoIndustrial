# 08 — Roadmap

## Concluído

| Fase | Entrega | Branch |
|---|---|---|
| 0 — Fundação | Projeto uv, FastAPI, configuração, logs, erros problem+json, Postgres+pgvector no Docker, Alembic, `/health`, `/ready`, testes com testcontainers | `feat/esqueleto-inicial` |
| 1 — Catálogo | Tipos de equipamento, fabricantes, famílias, equipamentos e documentos (metadados e vínculos N:N), com CRUD, filtros e paginação | `feat/catalogo` |

## Próximas fases

### 2 — Ingestão e busca semântica

- [ ] **Decidir o modelo de embedding** (define `vector(N)`):

  | Opção | Dimensão | Custo | Observação |
  |---|---|---|---|
  | Ollama + bge-m3 (local) | 1024 | Gratuito; precisa de CPU/GPU razoável | Multilíngue, bom em PT e EN |
  | OpenAI text-embedding-3-small | 1536 | Pago por uso | Sem infraestrutura local |

- [ ] Armazenamento de arquivos (pasta local, interface pronta para MinIO/S3).
- [ ] `POST /v1/documentos/{id}/arquivo`: upload do PDF, cálculo de `HASH_SHA256`, `CHAVE_ARQUIVO`, `TAMANHO_BYTES`.
- [ ] Processamento em segundo plano: extração de texto e tabelas, divisão em trechos por seção e tipo de conteúdo, geração de embeddings, atualização de `STATUS_PROCESSAMENTO`.
- [ ] Tabela `TRECHOS` com `EMBEDDING vector(N)`, índice HNSW e `tsvector` por idioma.
- [ ] `POST /v1/busca`: busca híbrida (vetorial + textual) com filtros por fabricante, família, modelo, tipo de documento, idioma e firmware.

### 3 — Dados estruturados

- [ ] Tabela `PARAMETROS` (código, descrição, unidade, faixa, valor padrão, por família e firmware).
- [ ] Tabela `FALHAS` (código, tipo falha/alarme, causa, solução).
- [ ] Extração assistida a partir das listas de parâmetros e de falhas.

### 4 — Agente de IA

- [ ] Endpoint de pergunta e resposta com citação das fontes (documento, página, seção).
- [ ] Ferramentas do agente: busca híbrida, consulta de parâmetro, consulta de falha.
- [ ] Histórico de conversas por usuário.

### 5 — Produção e clientes

- [ ] Autenticação JWT (pyjwt + pwdlib/argon2) e perfis de acesso.
- [ ] CORS para o frontend React.
- [ ] `Dockerfile` da API e pipeline de CI (ruff, mypy, pytest).
- [ ] Deploy (banco gerenciado com pgvector + container da API).
- [ ] Frontend React e aplicativo Android consumindo o OpenAPI.
