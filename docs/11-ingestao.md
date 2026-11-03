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
| `VOYAGE_MAX_TENTATIVAS` | `5` | Tentativas em 429/5xx/erro de rede |
| `VOYAGE_ESPERA_BASE_SEGUNDOS` | `10` | Base do backoff exponencial quando não há `Retry-After` |
| `VOYAGE_INTERVALO_MINIMO_SEGUNDOS` | `0` | Distância mínima entre chamadas ao Voyage (`0` = sem throttle) |

Em `ambiente=teste` a API usa `EmbeddingFake` (sem rede).

### Janela de contexto do modelo (400)

`voyage-context-4` aceita no máximo **32K tokens por lote** e não trunca. Se a Voyage
recusar o lote por excesso de tokens, o cliente **divide o lote ao meio e repete**
(recursivamente) até caber, mantendo a ordem dos vetores. Só falha se um único trecho
sozinho passar de 32K tokens — aí é preciso reduzir `INGESTAO_TAMANHO_TRECHO_CHARS`.

### Conta Voyage sem método de pagamento (429)

Sem cartão cadastrado a conta fica limitada a **3 RPM / 10K TPM**. Um lote padrão de
80.000 caracteres passa de 10K tokens, então toda requisição será recusada (o retry não
resolve sozinho porque o limite é por requisição). Ajuste no `backend/.env`:

```dotenv
INGESTAO_MAX_CHARS_LOTE_EMBEDDING=30000   # ~10K tokens por chamada
VOYAGE_INTERVALO_MINIMO_SEGUNDOS=21       # 3 requisições por minuto
```

Assim a ingestão completa mesmo no tier grátis, só que mais devagar (documentos grandes
levam alguns minutos). Cadastrar método de pagamento no dashboard do Voyage restaura os
limites normais e você pode voltar aos valores padrão.

## Código

| Módulo | Papel |
|---|---|
| `app/ingestao/extracao.py` | PDF → páginas |
| `app/ingestao/chunking.py` | páginas → candidatos |
| `app/ingestao/pipeline.py` | orquestração + tsvector |
| `app/documentos/fila.py` | agenda BackgroundTasks |
| `app/ia/fake.py` | embedding de teste |

## Próximo passo

Busca: [12 — Busca](12-busca.md). Roteiro em casa: [00 — Guia de teste manual](00-guia-teste-manual.md).
