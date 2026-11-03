# 14 — Agente Q&A

Endpoint `POST /v1/agente/perguntar`: recupera trechos com a **busca híbrida** e pede ao LLM uma resposta citada. O modelo não lê o PDF inteiro — só o contexto dos trechos retornados (economia de tokens).

O provedor é qualquer API compatível com o **OpenAI Chat Completions**: a chave, a URL base e o modelo vêm de `OPENAI_API_KEY`, `OPENAI_BASE_URL` e `LLM_MODELO`. O padrão do código é GPT-5 mini (`app/core/ia_defaults.py`), mas o provedor pode ser trocado só por configuração.

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
| `modelo_llm` | Modelo configurado em `LLM_MODELO` (padrão `gpt-5-mini`); `fake-llm` nos testes |
| `trechos_consultados` | Quantidade enviada ao LLM |

## Auth

Exige Bearer (`exigir_usuario`). Perfil `LEITURA` pode perguntar (somente leitura).

## Variáveis

| Variável | Uso |
|---|---|
| `OPENAI_API_KEY` | Chave do provedor de LLM. Obrigatória fora de `ambiente=teste` |
| `OPENAI_BASE_URL` | URL base do provedor (padrão `https://api.openai.com/v1`) |
| `LLM_MODELO` | Nome do modelo no provedor (padrão `gpt-5-mini`) |
| `LLM_MAX_TENTATIVAS` | Tentativas em 429/5xx/erro de rede (padrão `3`) |
| `LLM_ESPERA_BASE_SEGUNDOS` | Base do backoff exponencial (padrão `2`; `Retry-After` tem prioridade) |
| `VOYAGE_API_KEY` | Embedding da pergunta na busca |

O nome das variáveis segue o padrão do projeto e **não** limita o provedor: o cliente só faz `POST {OPENAI_BASE_URL}/chat/completions` com `Authorization: Bearer <OPENAI_API_KEY>`. Qualquer serviço que aceite esse contrato funciona.

| Provedor | `OPENAI_BASE_URL` | Exemplo de `LLM_MODELO` |
|---|---|---|
| OpenAI | `https://api.openai.com/v1` | `gpt-5-mini` |
| Google AI Studio | `https://generativelanguage.googleapis.com/v1beta/openai` | `gemini-3.8-flash` |
| OpenRouter | `https://openrouter.ai/api/v1` | `google/gemini-3.8-flash` |
| Ollama (local) | `http://localhost:11434/v1` | `llama3.1` |

Ao trocar de provedor, ajuste **as três** variáveis: a chave no formato do novo provedor, a URL base e um modelo que exista lá (manter `gpt-5-mini` fora da OpenAI resulta em erro 404 de modelo).

### Erro 503 com 404 no log (`openai_llm_http_erro`)

O agente devolve **503** quando o provedor recusa a chamada, e o motivo real fica no log,
no campo `detalhe`. Um 404 quase sempre significa nome de modelo inexistente ou
aposentado para a sua conta (ex.: `gemini-2.5-flash` responde que foi substituído por
`gemini-3.8-flash`). O retorno da API passa a citar o modelo e a URL base; corrija
`LLM_MODELO` no `backend/.env` e reinicie a API. Para listar os modelos da chave:
`GET {OPENAI_BASE_URL}/models`.

### 503 do provedor ("high demand")

Picos de demanda viram **503** no log (`openai_llm_http_erro`, status 503) e o cliente
repete a chamada com backoff exponencial antes de desistir. Com os padrões
(`LLM_MAX_TENTATIVAS=3`, `LLM_ESPERA_BASE_SEGUNDOS=2`) a espera total fica em poucos
segundos; se o pico persistir, a API responde 503 com mensagem de "sobrecarregado".
Aumentar as tentativas segura a requisição por mais tempo — prefira trocar de modelo ou
tentar novamente em instantes.

Os embeddings **não** mudam de provedor com essas variáveis: seguem na Voyage (`VOYAGE_API_KEY` / `EMBEDDING_MODELO`).

Rodando em Docker, `docker-compose.yml` / `docker-compose.prod.yml` repassam apenas `OPENAI_API_KEY`; `OPENAI_BASE_URL` e `LLM_MODELO` precisam ser adicionados ao bloco `environment` do serviço `api` para sair do padrão.

## Código

`app/agente/` — `router`, `service`, `deps`, `schemas`, `prompts`. Reutiliza `BuscaService` e `ProvedorLLM`.

## Ainda não nesta entrega

- Histórico de conversas por usuário.
- Streaming da resposta.
- Extração em lote a partir de PDFs de lista de parâmetros/falhas.

## Próximo passo

Roteiro de teste: [00 — Guia de teste manual](00-guia-teste-manual.md). Clientes React/Android; histórico de conversas.
