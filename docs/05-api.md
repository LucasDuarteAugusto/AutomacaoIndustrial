# 05 — API

A referência completa e interativa é gerada automaticamente em <http://127.0.0.1:8000/docs> (Swagger) e o contrato OpenAPI em <http://127.0.0.1:8000/openapi.json>. Este documento explica as convenções e dá exemplos.

## Convenções

| Item | Regra |
|---|---|
| Versionamento | Rotas de negócio sob `/v1/...`; `/health` e `/ready` ficam fora |
| Formato | JSON, campos em snake_case |
| IDs | UUID em texto |
| Datas | ISO 8601 com fuso (`2026-10-14T17:08:31.470412Z`) |
| Decimais | Número JSON (`5.5`) |
| Campos desconhecidos no corpo | Rejeitados (422) |
| Espaços nas pontas de textos | Removidos automaticamente |

| Operação | Método | Sucesso |
|---|---|---|
| Listar | `GET /v1/<recurso>` | 200 |
| Obter | `GET /v1/<recurso>/{id}` | 200 |
| Criar | `POST /v1/<recurso>` | 201 |
| Alterar parcialmente | `PATCH /v1/<recurso>/{id}` | 200 |
| Excluir | `DELETE /v1/<recurso>/{id}` | 204 (sem corpo) |

## Paginação

Toda listagem aceita `limit` (1–100, padrão 20) e `offset` (padrão 0) e responde:

```json
{ "items": [ ... ], "total": 42 }
```

`total` é a quantidade total que atende aos filtros (não só a página). Página 3 com 20 itens: `?limit=20&offset=40`.

## Autenticação

Rotas `/v1/...` exigem `Authorization: Bearer <token>`, exceto `POST /v1/auth/login` e `POST /v1/auth/bootstrap`. Detalhes e perfis: [13 — Auth](13-auth.md).

## Rotas

### Health

| Rota | Resposta |
|---|---|
| `GET /health` | `{"status": "ok"}` se o processo está vivo |
| `GET /ready` | `{"status": "ok"}` se o banco responde; 503 caso contrário |

### Auth — `/v1/auth`

| Rota | Descrição |
|---|---|
| `POST /bootstrap` | Primeiro ADMIN (só com base vazia) |
| `POST /login` | E-mail + senha → JWT |
| `GET /me` | Usuário do token |
| `POST /usuarios`, `PATCH /usuarios/{id}` | CRUD de usuários (`ADMIN`) |

### Agente — `/v1/agente`

| Rota | Descrição |
|---|---|
| `POST /perguntar` | Q&A com busca híbrida + LLM e citações (documento, página, seção) |

Detalhes: [14 — Agente](14-agente.md).

### Tipos de equipamento — `/v1/tipos-equipamento`

Somente leitura (cadastrados por migration). `GET` lista e `GET /{id}`.

### Fabricantes — `/v1/fabricantes`

| Filtro | Descrição |
|---|---|
| `busca` | Texto contido no nome (sem diferenciar maiúsculas) |
| `ativo` | `true` / `false` |

Corpo de criação: `nome` (obrigatório, até 100), `site` (opcional), `ativo` (padrão `true`).

### Famílias — `/v1/familias`

| Filtro | Descrição |
|---|---|
| `id_fabricante` | Famílias de um fabricante |
| `id_tipo_equipamento` | Famílias de um tipo |
| `busca`, `ativo` | Como em fabricantes |

Corpo de criação: `id_fabricante`, `id_tipo_equipamento`, `nome` (até 150), `descricao`, `ativo`.

### Equipamentos — `/v1/equipamentos`

| Filtro | Descrição |
|---|---|
| `id_familia` | Modelos de uma família |
| `busca` | Texto no código de pedido ou no nome |
| `ativo` | `true` / `false` |

Corpo de criação: `id_familia`, `codigo_pedido` (até 60), `nome` (até 200), `potencia_kw`, `tensao_nominal_v`, `corrente_nominal_a` (opcionais, não negativos), `ativo`.

### Documentos — `/v1/documentos`

| Filtro | Descrição |
|---|---|
| `id_familia` | Documentos que cobrem a família |
| `id_equipamento` | Documentos ligados ao modelo |
| `tipo_documento` | `MANUAL_OPERACAO`, `LISTA_PARAMETROS`, `GUIA_RAPIDO`, `MANUAL_COMUNICACAO`, `DATASHEET`, `NOTA_APLICACAO` |
| `idioma` | `pt-BR` ou `en` |
| `busca` | Texto no título ou no código do documento |

Corpo de criação: `titulo`, `tipo_documento`, `idioma`, `codigo_documento`, `edicao`, `versao_firmware`, `ids_familias` (pelo menos 1), `ids_equipamentos` (opcional; cada equipamento precisa pertencer a uma das famílias informadas).

No `PATCH`, enviar `ids_familias` ou `ids_equipamentos` **substitui** a lista inteira.

Campos de arquivo (ingestão): `chave_arquivo`, `hash_sha256`, `tamanho_bytes`, `paginas`, `status_processamento`, `erro_processamento`.

#### Upload do PDF — `POST /v1/documentos/{id}/arquivo`

`multipart/form-data` com o campo `arquivo` (PDF). Valida assinatura `%PDF-`, calcula SHA-256, grava no armazenamento e atualiza os metadados. Resposta `200` com `DocumentoOut`.

| Situação | Status |
|---|---|
| PDF ok (novo ou mesma hash no mesmo documento) | 200 |
| Documento inexistente | 404 |
| Mesmo arquivo já ligado a **outro** documento | 409 |
| Não é PDF / vazio / acima do limite | 422 |

Limite: `ARMAZENAMENTO_TAMANHO_MAX_BYTES` (padrão 50 MiB). Após o upload, a ingestão roda em background (síncrona em `ambiente=teste`): preenche `paginas`, grava `TRECHOS` e passa a `INDEXADO` (ou `ERRO`). Trocar o PDF (hash diferente) apaga o arquivo antigo e os trechos. Excluir o documento também remove o arquivo do armazenamento.

#### Reprocessar — `POST /v1/documentos/{id}/reprocessar`

Roda de novo o pipeline sobre o PDF já armazenado (sem novo upload). `409` se já estiver `PROCESSANDO`. Detalhes em [11 — Ingestão](11-ingestao.md).

### Busca — `/v1/busca`

`POST /v1/busca` com JSON: `consulta` (obrigatória), `limit` (1–50), filtros opcionais (`id_fabricante`, `id_familia`, `id_equipamento`, `tipo_documento`, `idioma`, `versao_firmware`).

Resposta: `{ consulta, items, total }` — trechos ranqueados por RRF (semântica + textual). Detalhes em [12 — Busca](12-busca.md).

```powershell
Invoke-RestMethod -Method Post "$api/v1/busca" -ContentType $ct -Body (Json @{
  consulta = "tempo de rampa p1120"
  limit = 5
})
```

```powershell
$id = "<uuid-do-documento>"
Invoke-RestMethod -Method Post "$api/v1/documentos/$id/arquivo" -Form @{
  arquivo = Get-Item ".\manual.pdf"
}
```

## Exemplo completo

```powershell
$api = "http://127.0.0.1:8000"
function Json($obj) { [Text.Encoding]::UTF8.GetBytes(($obj | ConvertTo-Json)) }
$ct = "application/json; charset=utf-8"

$fab = Invoke-RestMethod -Method Post "$api/v1/fabricantes" -ContentType $ct -Body (Json @{
  nome = "Siemens"; site = "https://www.siemens.com"
})

$tipo = (Invoke-RestMethod "$api/v1/tipos-equipamento").items | Where-Object codigo -eq "INVERSOR"

$fam = Invoke-RestMethod -Method Post "$api/v1/familias" -ContentType $ct -Body (Json @{
  id_fabricante = $fab.id_fabricante; id_tipo_equipamento = $tipo.id_tipo_equipamento; nome = "SINAMICS G120"
})

$eq = Invoke-RestMethod -Method Post "$api/v1/equipamentos" -ContentType $ct -Body (Json @{
  id_familia = $fam.id_familia; codigo_pedido = "6SL3210-1KE21-3UF1"; nome = "PM240-2 5,5 kW 400 V"
  potencia_kw = 5.5; tensao_nominal_v = 400
})

Invoke-RestMethod -Method Post "$api/v1/documentos" -ContentType $ct -Body (Json @{
  titulo = "SINAMICS G120 - Lista de parâmetros"; tipo_documento = "LISTA_PARAMETROS"; idioma = "pt-BR"
  ids_familias = @($fam.id_familia); ids_equipamentos = @($eq.id_equipamento)
})
```

A função `Json` converte o corpo para bytes UTF-8. Sem ela, o Windows PowerShell 5 envia acentos ("parâmetros") com codificação errada.

Resposta do documento (resumida):

```json
{
  "id_documento": "0b7e…",
  "titulo": "SINAMICS G120 - Lista de parâmetros",
  "tipo_documento": "LISTA_PARAMETROS",
  "idioma": "pt-BR",
  "status_processamento": "PENDENTE",
  "familias": [{ "id_familia": "5c1a…", "nome": "SINAMICS G120" }],
  "equipamentos": [{ "id_equipamento": "9d2f…", "codigo_pedido": "6SL3210-1KE21-3UF1", "nome": "PM240-2 5,5 kW 400 V" }],
  "created_at": "2026-10-14T17:08:31.470412Z",
  "updated_at": "2026-10-14T17:08:31.470412Z"
}
```

## Erros (RFC 9457)

Todo erro tem `Content-Type: application/problem+json`:

```json
{
  "type": "about:blank",
  "title": "Conflito",
  "status": 409,
  "detail": "O fabricante já possui uma família chamada 'SINAMICS G120'.",
  "instance": "/v1/familias"
}
```

| Status | Quando | Exemplo |
|---|---|---|
| 404 | Recurso ou rota não existe | `GET /v1/fabricantes/{id-inexistente}` |
| 409 | Duplicidade ou exclusão bloqueada por vínculo | Nome de fabricante repetido; excluir família com equipamentos |
| 422 | Corpo/parâmetro inválido ou referência inexistente | Nome vazio; `limit=500`; `id_fabricante` que não existe; equipamento de outra família |
| 500 | Erro inesperado (registrado no log, sem detalhes ao cliente) | — |
| 503 | Dependência indisponível | `/ready` sem banco |

Erros de validação trazem a lista de campos em `errors`:

```json
{
  "title": "Dados de entrada inválidos",
  "status": 422,
  "detail": "Um ou mais campos não passaram na validação.",
  "instance": "/v1/equipamentos",
  "errors": [{ "loc": ["body", "potencia_kw"], "msg": "Input should be greater than or equal to 0", "type": "greater_than_equal" }]
}
```

## Gerando cliente para o frontend

Como o contrato é OpenAPI, React e Android podem gerar clientes tipados:

```powershell
# TypeScript (React)
npx openapi-typescript http://127.0.0.1:8000/openapi.json -o src/api/schema.d.ts

# Kotlin (Android) com openapi-generator
npx @openapitools/openapi-generator-cli generate -i http://127.0.0.1:8000/openapi.json -g kotlin -o android-client
```
