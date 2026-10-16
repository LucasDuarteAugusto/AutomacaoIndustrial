# 10 — Armazenamento de arquivos

PDFs dos manuais ficam **fora do Postgres**. O banco guarda só metadados (`CHAVE_ARQUIVO`, `HASH_SHA256`, `TAMANHO_BYTES`, `PAGINAS`, `STATUS_PROCESSAMENTO`).

Decisão desta fatia (`feat/armazenamento-local`):

- **Agora:** armazenamento **local** em disco.
- **Pronto no código:** adaptador **S3-compatível** para Cloudflare R2 (e, mais à frente, AWS S3), sem MinIO no compose.
- **Ainda não:** endpoint HTTP de upload (próxima fatia).

## Variáveis (`backend/.env`)

Copie `backend/.env.example` → `backend/.env`. A tabela abaixo cobre o bloco de armazenamento; o restante (banco, Voyage, OpenAI) está em [01 — Rodando localmente](01-rodando-localmente.md).

### Modo local (padrão — use para desenvolver e testar)

| Variável | Preencher? | Exemplo | Descrição |
|---|---|---|---|
| `ARMAZENAMENTO_TIPO` | Sim | `local` | Seleciona a implementação |
| `ARMAZENAMENTO_CAMINHO` | Sim | `data/arquivos` | Pasta relativa a `backend/` (ou caminho absoluto) |

Arquivo em disco: `{ARMAZENAMENTO_CAMINHO}/{id_documento}/{sha256}.pdf`.  
A pasta `backend/data/` está no `.gitignore`.

Com `ARMAZENAMENTO_TIPO=local`, as variáveis `S3_*` podem ficar vazias.

### Modo S3 / Cloudflare R2 (quando migrar para nuvem gratuita)

Defina `ARMAZENAMENTO_TIPO=s3` e preencha:

| Variável | Preencher? | Exemplo R2 | Descrição |
|---|---|---|---|
| `S3_ENDPOINT_URL` | Sim (R2) | `https://<accountid>.r2.cloudflarestorage.com` | Endpoint do account R2 |
| `S3_REGION` | Sim | `auto` | No R2 use `auto` |
| `S3_BUCKET` | Sim | `automacao-industrial` | Nome do bucket |
| `S3_ACCESS_KEY_ID` | Sim | *(token R2)* | Access Key ID |
| `S3_SECRET_ACCESS_KEY` | Sim | *(secret R2)* | Secret Access Key |

Passos no painel Cloudflare: criar bucket R2 → criar API token com permissão de objeto no bucket → colar endpoint e chaves no `.env`.

Free tier típico do R2 (verifique a lista atual da Cloudflare): ~10 GB/mês, operações generosas, egress grátis.

### AWS S3 (produção futura)

Mesmo `ARMAZENAMENTO_TIPO=s3` e mesmas chaves `S3_BUCKET` / `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY`. Em geral **omita** `S3_ENDPOINT_URL` (ou use o endpoint regional) e ajuste `S3_REGION` (`us-east-1`, etc.). Não é necessário agora.

## Contrato no código

Interface `ArmazenamentoArquivos`:

| Método | Comportamento |
|---|---|
| `salvar(chave, conteudo, content_type=...)` | Grava ou sobrescreve |
| `carregar(chave)` | Lê bytes; `FileNotFoundError` se ausente |
| `existe(chave)` | `True` / `False` |
| `apagar(chave)` | Remove se existir (no-op se já não houver) |

Chave portátil entre local e nuvem:

```text
chave_documento(id_documento, hash_sha256) → "{uuid}/{64 hex}.pdf"
```

| Módulo | Papel |
|---|---|
| `app/armazenamento/base.py` | Protocolo |
| `app/armazenamento/local.py` | Disco (`asyncio.to_thread`; bloqueia path traversal) |
| `app/armazenamento/s3.py` | R2 / AWS via `aioboto3` |
| `app/armazenamento/chave.py` | Montagem e validação da chave |
| `app/armazenamento/factory.py` | Escolha pelo `Settings` |
| `app/armazenamento/deps.py` | `ArmazenamentoDep` no FastAPI |
| `app/main.py` (lifespan) | Cria `app.state.armazenamento` |

Dependência: `aioboto3` (cliente S3 async). Só é usado de fato com `ARMAZENAMENTO_TIPO=s3`.

## Testes

```powershell
cd backend
uv run pytest tests/armazenamento -q
```

Local usa `tmp_path`; S3 usa mocks do cliente (sem rede / sem conta).

## Upload HTTP

`POST /v1/documentos/{id}/arquivo` (multipart, campo `arquivo`). Detalhes e códigos de erro em [05 — API](05-api.md).

Fluxo: validar PDF → SHA-256 → `chave_documento` → `armazenamento.salvar` → atualizar `DOCUMENTOS`. Status permanece `PENDENTE` até o pipeline de trechos (próxima fatia).

| Variável | Padrão | Uso |
|---|---|---|
| `ARMAZENAMENTO_TAMANHO_MAX_BYTES` | `52428800` (50 MiB) | Limite do corpo do upload |

## Próximo passo

Busca híbrida: ver [11 — Ingestão](11-ingestao.md) (pipeline já implementado) e depois `POST /v1/busca`.
