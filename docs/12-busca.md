# 12 — Busca híbrida

Endpoint `POST /v1/busca`: combina proximidade semântica (pgvector / cosseno) com busca textual (`tsvector`), fundidas por **RRF** (Reciprocal Rank Fusion).

## Entrada

```json
{
  "consulta": "tempo de rampa p1120",
  "limit": 10,
  "id_fabricante": null,
  "id_familia": null,
  "id_equipamento": null,
  "tipo_documento": null,
  "idioma": null,
  "versao_firmware": null
}
```

Filtros opcionais restritos a documentos `INDEXADO` com trechos embutidos.

## Saída

Lista de trechos com `score` (RRF), `distancia_cosseno` (menor = mais próximo), `rank_textual`, metadados do documento e localização (`secao`, `pagina`).

## Como funciona

1. Embedding da consulta (`embed_consulta` / Voyage ou fake em teste).
2. Top-N candidatos por distância de cosseno.
3. Top-N candidatos por `ts_rank_cd` + `plainto_tsquery` (config `portuguese` ou `english` conforme o idioma do documento).
4. Funde com \( \frac{1}{k + rank} \) em cada lista (`BUSCA_RRF_K`, padrão 60).

## Variáveis

| Variável | Padrão | Descrição |
|---|---|---|
| `BUSCA_CANDIDATOS_POR_MODO` | `40` | Tamanho de cada ranking antes do RRF |
| `BUSCA_RRF_K` | `60` | Constante RRF |
| `VOYAGE_API_KEY` | — | Necessária fora de `ambiente=teste` |

## Código

`app/busca/` — `router`, `service`, `repository`, `schemas`.

## Próximo passo

Auth: [13 — Autenticação](13-auth.md). Em seguida: agente Q&A usando esta busca.
