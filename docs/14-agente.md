# 14 — Agente Q&A

Endpoint `POST /v1/agente/perguntar`: recupera trechos com a **busca híbrida** e pede ao LLM (GPT-5 mini) uma resposta citada. O modelo não lê o PDF inteiro — só o contexto dos trechos retornados (economia de tokens).

## Fluxo

```text
pergunta (+ filtros opcionais)
  → extrai códigos (p1120, F07801, …) → consulta PARAMETROS / FALHAS
  → BuscaService (vetor + tsvector + RRF)
  → se não houver trechos nem registros: resposta fixa sem chamar o LLM
  → senão: prompt com [P#]/[F#] + trechos [1]…[N] → ProvedorLLM.completar
  → resposta + citações + listas `parametros` / `falhas`
```

## Entrada

```json
{
  "pergunta": "Qual parâmetro controla o tempo de rampa?",
  "limit": 8,
  "id_fabricante": null,
  "id_familia": null,
  "id_equipamento": null,
  "tipo_documento": null,
  "idioma": null,
  "versao_firmware": null
}
```

`limit` padrão **8** (máx. 20): quantos trechos entram no contexto do LLM. Filtros iguais aos de [12 — Busca](12-busca.md).

## Saída

| Campo | Descrição |
|---|---|
| `resposta` | Texto gerado (ou aviso se não houver trechos) |
| `citacoes` | Fontes `[1]…[N]` com `id_documento`, `titulo_documento`, `pagina`, `secao`, `trecho`, `score` |
| `parametros` / `falhas` | Hits estruturados quando a pergunta cita códigos conhecidos |
| `modelo_llm` | Modelo usado (`gpt-5-mini` em produção; `fake-llm` nos testes) |
| `trechos_consultados` | Quantidade enviada ao LLM |

## Auth

Exige Bearer (`exigir_usuario`). Perfil `LEITURA` pode perguntar (somente leitura).

## Variáveis

| Variável | Uso |
|---|---|
| `OPENAI_API_KEY` | Obrigatória fora de `ambiente=teste` |
| `OPENAI_BASE_URL` / `LLM_MODELO` | Cliente Chat Completions (padrão GPT-5 mini) |
| `VOYAGE_API_KEY` | Embedding da pergunta na busca |

## Código

`app/agente/` — `router`, `service`, `deps`, `schemas`, `prompts`. Reutiliza `BuscaService` e `ProvedorLLM`.

## Ainda não nesta entrega

- Histórico de conversas por usuário.
- Streaming da resposta.
- Extração em lote a partir de PDFs de lista de parâmetros/falhas.

## Próximo passo

Roteiro de teste: [00 — Guia de teste manual](00-guia-teste-manual.md). Clientes React/Android; histórico de conversas.
