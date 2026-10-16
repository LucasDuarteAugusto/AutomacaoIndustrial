# 11 — Pipeline de ingestão

Transforma o PDF anexado ao documento em trechos pesquisáveis (`TRECHOS` com embedding + `tsvector`).

## Fluxo

```text
POST /v1/documentos/{id}/arquivo
        │
        ▼
  grava PDF + metadados (PENDENTE)
        │
        ▼
  ┌─ ambiente=teste: síncrono na mesma sessão
  └─ local/produção: BackgroundTasks (nova sessão)
        │
        ▼
  PROCESSANDO
        │
        ├─ PyMuPDF: texto por página (+ TOC → seção)
        ├─ chunking sem overlap (~2500 caracteres)
        ├─ Voyage voyage-context-4 (lotes se o doc for grande)
        ├─ grava TRECHOS + to_tsvector (portuguese | english)
        └─ INDEXADO  (ou ERRO + mensagem)
```

Reprocessar sem novo upload: `POST /v1/documentos/{id}/reprocessar`.

## Variáveis

| Variável | Padrão | Descrição |
|---|---|---|
| `VOYAGE_API_KEY` | — | Obrigatória fora de `ambiente=teste` |
| `INGESTAO_TAMANHO_TRECHO_CHARS` | `2500` | Tamanho alvo de cada trecho |
| `INGESTAO_MAX_CHARS_LOTE_EMBEDDING` | `80000` | Janela máxima por chamada contextualizada ao Voyage |

Em `ambiente=teste` a API usa `EmbeddingFake` (sem rede).

## Código

| Módulo | Papel |
|---|---|
| `app/ingestao/extracao.py` | PDF → páginas |
| `app/ingestao/chunking.py` | páginas → candidatos |
| `app/ingestao/pipeline.py` | orquestração + tsvector |
| `app/documentos/fila.py` | agenda BackgroundTasks |
| `app/ia/fake.py` | embedding de teste |

## Próximo passo

Busca já disponível: [12 — Busca](12-busca.md). Em seguida: JWT + CORS e o agente Q&A.
