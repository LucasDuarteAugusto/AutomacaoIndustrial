# 14 — Agente Q&A

Endpoint `POST /v1/agente/perguntar`: recupera trechos com a **busca híbrida** e pede ao LLM (GPT-5 mini) uma resposta citada. O modelo não lê o PDF inteiro — só o contexto dos trechos retornados (economia de tokens).

## Fluxo

```text
pergunta (+ filtros opcionais)
  → BuscaService (vetor + tsvector + RRF)
  → se não houver trechos: resposta fixa sem chamar o LLM
  → senão: prompt com trechos [1]…[N] → ProvedorLLM.completar
  → resposta + lista de citações (documento, página, seção, trecho)
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

- Ferramentas de `PARAMETROS` / `FALHAS` (fase 3).
- Histórico de conversas por usuário.
- Streaming da resposta.

## Próximo passo

Dados estruturados (`PARAMETROS` / `FALHAS`) para o agente consultar códigos com precisão; depois Docker/CI.
