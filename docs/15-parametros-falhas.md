# 15 — Parâmetros e falhas estruturados

Tabelas `PARAMETROS` e `FALHAS` guardam códigos de comissionamento de forma consultável (exata), complementando a busca híbrida em trechos. O agente extrai códigos da pergunta (`p1120`, `F07801`, …) e injeta esses registros no contexto do LLM.

## Escopo

| Campo comum | Uso |
|---|---|
| `id_familia` | Família do equipamento (obrigatório) |
| `versao_firmware` | Opcional; `null` = vale para qualquer firmware |
| `codigo` | Código do parâmetro ou da falha/alarme |
| `idioma` | `pt-BR` ou `en` |
| `id_documento` / `pagina` | Proveniência opcional |

Unicidade: mesma família + código (case-insensitive) + idioma + firmware (nulo tratado como escopo único).

## PARAMETROS — `/v1/parametros`

Campos principais: `nome`, `descricao`, `unidade`, `valor_min` / `valor_max`, `valor_padrao`, `grupo`, `somente_leitura`.

Filtros de listagem: `id_familia`, `codigo`, `versao_firmware`, `idioma`, `busca`, `ativo`.

## FALHAS — `/v1/falhas`

Campos principais: `tipo` (`FALHA` \| `ALARME`), `titulo`, `descricao`, `causa`, `solucao`, `reacao`.

Filtros: `id_familia`, `codigo`, `tipo`, `versao_firmware`, `idioma`, `busca`, `ativo`.

## Auth

Leitura: qualquer usuário autenticado. Escrita: `ADMIN` / `OPERADOR` (`exigir_operacao_escrita`).

## Agente

`POST /v1/agente/perguntar` devolve também `parametros` e `falhas` quando a pergunta cita códigos reconhecidos. Ver [14 — Agente](14-agente.md).

## Código

`app/parametros/`, `app/falhas/` — models, repository, service, router, schemas. Migration `cria_parametros_e_falhas`.

## Ainda não

Extração assistida a partir de PDFs `LISTA_PARAMETROS` / listas de falhas (preenchimento em lote).

## Próximo passo

Docker/CI; histórico de conversas do agente; clientes React/Android.
