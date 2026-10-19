# 21 — Estudo: frontend React

Estudo para criar o frontend web da plataforma (pasta `frontend/`, irmã de `backend/`). Cobre a escolha da stack com versões, a arquitetura, a integração com a API, as telas, a qualidade, o deploy, as lacunas do backend e um plano de entrega.

Versões consultadas no registro npm e em `nodejs.org` em **19/10/2026**.

## Resumo da decisão

| Tema | Decisão |
|---|---|
| Tipo de aplicação | **SPA** (Vite) servida como arquivos estáticos pelo nginx que já existe no deploy |
| Runtime / gerenciador | **Node.js 24 LTS** + **pnpm 11** |
| Linguagem | **TypeScript 6.0** (strict) |
| UI | **React 19.3**, **Tailwind CSS 4.3**, componentes **shadcn/ui** (Radix) |
| Rotas | **TanStack Router** (rotas tipadas, filtros validados na URL) |
| Dados do servidor | **TanStack Query 5** |
| Cliente da API | Gerado do OpenAPI com **Orval 8** (hooks de query, schemas Zod e mocks MSW) |
| Formulários | **React Hook Form 7** + **Zod 4** |
| Testes | **Vitest 4.1** + Testing Library + **MSW 2**; E2E com **Playwright** |
| Lint / formatação | **ESLint 9** (flat config) + typescript-eslint + **Prettier 3** |
| Deploy | Imagem `nginx:1.30-alpine` com o build; mesma origem da API (sem CORS em produção) |

## 1. O que o backend oferece ao frontend

Resumo do contrato que o frontend vai consumir. A referência é o OpenAPI (`/openapi.json`) e o [05 — API](05-api.md).

| Aspecto | Como funciona hoje | Impacto no frontend |
|---|---|---|
| Rotas | Negócio em `/v1/...`; `/health` e `/ready` fora | Proxy do Vite e do nginx só precisa de `/v1`, `/health`, `/ready` |
| Autenticação | `POST /v1/auth/login` devolve JWT Bearer (HS256), `expires_in` = 8 h, **sem refresh token** | Sessão dura um turno; ao expirar, novo login |
| Perfis | `ADMIN` (tudo + usuários), `OPERADOR` (leitura e escrita), `LEITURA` (só leitura; pode perguntar ao agente) | Esconder ações de escrita para `LEITURA`; área de usuários só para `ADMIN`. O backend continua sendo quem garante (403) |
| Paginação | `?limit=` (1–100, padrão 20) e `?offset=` → `{ items, total }` | Tabelas com paginação no servidor; selects de família/equipamento precisam de busca no servidor (`busca`), não carregar tudo |
| Campos | JSON em `snake_case`, UUID em texto, datas ISO 8601 com fuso, decimais como número | Manter `snake_case` nos tipos gerados (sem camada de conversão) |
| Erros | RFC 9457 `application/problem+json` (`title`, `status`, `detail`, `instance`); 422 traz `errors[]` com `loc` | Um único tratador de erros; 422 mapeado para campos do formulário |
| Exclusão com vínculo | 409 com orientação para desativar (`ativo=false`) | Diálogo de exclusão oferece "Desativar" quando der 409 |
| Upload | `POST /v1/documentos/{id}/arquivo` multipart, PDF até 50 MiB | Upload com barra de progresso |
| Ingestão | Assíncrona: `PENDENTE` → `PROCESSANDO` → `INDEXADO` ou `ERRO` | Atualização automática do status (polling) enquanto processa |
| Busca | `POST /v1/busca` (vetor + textual + RRF), filtros por fabricante/família/equipamento/tipo/idioma/firmware | Tela de busca com filtros e trechos ranqueados |
| Agente | `POST /v1/agente/perguntar` → `resposta` + `citacoes[]` + `parametros[]` + `falhas[]`; **sem streaming** e **sem histórico** | Estado de carregamento longo, cancelamento, histórico local |
| Rate limit | Por IP e por minuto: auth 20, agente 20, busca 60, demais 120; 429 com `Retry-After` | Avisar e aguardar o `Retry-After`; evitar refetch agressivo |
| CORS | `CORS_ORIGINS` padrão `http://localhost:5173,http://localhost:3000` | Porta 5173 (Vite) já liberada |
| Enums | `TipoDocumento`, `Idioma` (`pt-BR`/`en`), `StatusProcessamento`, `Perfil`, `TipoFalha` (`FALHA`/`ALARME`) | Viram tipos no cliente gerado; o frontend só mantém os rótulos em português |

Um detalhe útil: com `AMBIENTE=teste`, a API usa embedding e LLM falsos (`EmbeddingFake`, `LLMFake`), o que permite testes E2E determinísticos sem chaves da Voyage/OpenAI.

## 2. Critério de "moderna porém consolidada"

Mesma filosofia do backend (pin de versão, sem subir major de passagem), em regra objetiva:

1. **Runtime**: só linha **LTS ativa** do Node.js.
2. **Bibliotecas**: o major escolhido precisa ter **pelo menos ~6 meses** de lançamento, vários minors/patches, e o ecossistema ao redor (plugins, tipos, ferramentas) precisa **declarar suporte** a ele nos `peerDependencies`.
3. Major recém-lançado fica em observação até cumprir o item 2.

### Versões

| Peça | Usar | Evitar por enquanto | Motivo |
|---|---|---|---|
| Node.js | **24.22** (LTS "Krypton") | 26.x | 26 ainda é "Current" (lançado em mai/2026); deve virar LTS no fim de out/2026. Reavaliar em 2027 |
| pnpm | **11.28** | 12.x | 12 saiu em ago/2026 |
| TypeScript | **6.0.3** | 7.0 | 7.0 (compilador nativo em Go) saiu em jul/2026 e o `typescript-eslint` 8.71 só aceita `<6.1`. O 6.0 já marca como obsoleto o que o 7 remove, então a migração futura fica simples |
| React / react-dom | **19.3** | — | Major 19 desde dez/2024 |
| Vite | **8.3** + `@vitejs/plugin-react` **6.1** | — | Major 8 desde mar/2026 (bundler Rolldown); Vitest 4.1, Tailwind e TanStack Router já declaram `vite ^8`. Plano B: Vite 7.3 + plugin-react 5.2 |
| TanStack Router | **1.170** + `@tanstack/router-plugin` 1.168 | React Router 8 | React Router 8 saiu em jun/2026 |
| TanStack Query | **5.104** | — | Major 5 desde out/2023 |
| TanStack Table | **8.21** | 9.x | 9 saiu em ago/2026 |
| TanStack Virtual | **3.14** | — | Listas longas de parâmetros/falhas |
| Orval | **8.43** | — | Major 8 desde jan/2026; exige Node ≥ 22.18 |
| Zod | **4.6** | — | Major 4 desde jul/2025 |
| React Hook Form | **7.90** + `@hookform/resolvers` **5.9** | resolvers 6.0 | resolvers 6.0 foi publicado hoje |
| Tailwind CSS | **4.3** + `@tailwindcss/vite` 4.3 | — | Major 4 desde jan/2025 |
| shadcn/ui (CLI) | **4.x** + `radix-ui` 1.8 | — | Componentes copiados para o projeto (não é dependência de runtime) |
| Ícones | `lucide-react` **1.59** | — | |
| Toasts | `sonner` **2.0** | — | |
| Markdown (resposta do agente) | `react-markdown` **10.1** + `remark-gfm` **4.0** | — | Sem HTML bruto (seguro contra XSS) |
| Visualizador de PDF | `react-pdf` **10.5** (com o `pdfjs-dist` que ele traz) | react-pdf 11 | 11 saiu em set/2026 |
| Estado de cliente | `zustand` **5.0** (só se precisar) | — | A maior parte do estado é do servidor (Query) ou da URL (Router) |
| Testes unitários | `vitest` **4.1** + `@testing-library/react` **16.3** | Vitest 5 | 5 saiu em set/2026 |
| Mocks de API | `msw` **2.15** | MSW 3 | 3 saiu em set/2026 |
| E2E | `@playwright/test` **1.64** | — | |
| Lint | `eslint` **9.39** + `typescript-eslint` 8.71 + `eslint-plugin-react-hooks` 7.1 + `eslint-plugin-jsx-a11y` 6.10 + `@tanstack/eslint-plugin-query` 5 | ESLint 10 | `eslint-plugin-jsx-a11y` ainda não declara suporte ao ESLint 10 |
| Formatação | `prettier` **3.9** | — | |
| React Compiler | `babel-plugin-react-compiler` **1.0** (opcional) | — | Memoização automática; com plugin-react 6 entra via `@rolldown/plugin-babel`. Ligar na fundação se a prova de conceito não mostrar problema |
| Servidor estático | `nginx:1.30-alpine` (stable) | 1.31 (mainline) | O `docker-compose.scale.yml` ainda usa `nginx:1.27-alpine`; atualizar junto |

Ficam de fora no início: Storybook (custo de manutenção alto para um time pequeno), i18n (a interface começa só em pt-BR; os textos ficam centralizados para facilitar adotar `i18next` 26 / `react-i18next` 17 se precisar de inglês) e bibliotecas de data (a API `Intl` do navegador formata datas e números em pt-BR).

### Proteção da cadeia de suprimentos

O pnpm permite recusar versões publicadas há pouco tempo, o que reforça o critério acima e protege contra pacotes comprometidos:

```yaml
# frontend/pnpm-workspace.yaml
minimumReleaseAge: 10080   # minutos (7 dias)
```

O pnpm também não executa scripts de `postinstall` de dependências sem autorização explícita. Atualizações via Renovate ou Dependabot, agrupadas por família (TanStack, ESLint, testes), com major sempre em PR separado.

## 3. Arquitetura

### Por que SPA (e não Next.js ou SSR)

- É uma ferramenta interna autenticada: não há SEO nem página pública.
- O backend já é a FastAPI; SSR exigiria mais um servidor Node em produção, com sessão, deploy e monitoramento próprios.
- O build vira arquivos estáticos servidos pelo **nginx que já faz o balanceamento** da API (`deploy/nginx.conf`), na mesma origem. Sem CORS em produção e sem infraestrutura nova.
- O aplicativo Android planejado consome a mesma API; a lógica fica no backend, não no servidor do frontend.

### Visão geral

```text
Navegador (SPA React)
   │  mesma origem (https://automacao.exemplo)
   ▼
nginx ─┬─ /                  → arquivos estáticos do build (fallback para index.html)
       ├─ /v1/, /health, /ready → api:8000 (réplicas, DNS round-robin)
       └─ (Swagger /docs só fora de produção)
                                   │
                                   ▼
                     FastAPI → PostgreSQL + pgvector (+ Redis)
```

Em desenvolvimento, o Vite faz o mesmo papel com `server.proxy`, então o código sempre chama caminhos relativos (`/v1/...`).

### Camadas no frontend

| Camada | Responsabilidade | Ferramenta |
|---|---|---|
| Rotas | URL, layout, guarda de autenticação/perfil, filtros e paginação na query string | TanStack Router |
| Estado do servidor | Cache, refetch, invalidação após mutação, polling | TanStack Query (hooks gerados pelo Orval) |
| Cliente HTTP | Header `Authorization`, parse de problem+json, 401/429 | `src/api/http.ts` (mutator do Orval) |
| Formulários | Validação com os mesmos limites do backend | React Hook Form + schemas Zod gerados |
| UI | Componentes acessíveis e tema | shadcn/ui + Tailwind |
| Estado local | Sessão (token, usuário), preferências (tema) | Contexto React ou Zustand |

## 4. Integração com a API

### Cliente gerado (Orval)

O backend gera o contrato (Pydantic → OpenAPI). O Orval transforma o contrato em:

- tipos TypeScript dos schemas (`DocumentoOut`, `FamiliaCreate`, …);
- hooks do TanStack Query (`useListarDocumentos`, `useCriarFamilia`, …) com chaves de cache prontas;
- schemas Zod com os mesmos limites do Pydantic (`max_length`, `ge`, `min_length`), usados nos formulários;
- handlers do MSW com dados falsos, usados nos testes.

Assim, um limite alterado no Pydantic chega ao formulário do frontend sem digitar nada à mão.

```ts
// frontend/orval.config.ts
import { defineConfig } from "orval";

export default defineConfig({
  api: {
    input: "./openapi.json",
    output: {
      target: "src/api/gerado/endpoints.ts",
      schemas: "src/api/gerado/modelos",
      client: "react-query",
      httpClient: "fetch",
      mode: "tags-split",
      mock: true,
      override: {
        mutator: { path: "src/api/http.ts", name: "http" },
      },
    },
  },
  zod: {
    input: "./openapi.json",
    output: { target: "src/api/gerado/zod", client: "zod", mode: "tags-split" },
  },
});
```

Alternativa mais enxuta: `openapi-typescript` + `openapi-fetch` + `openapi-react-query` (só tipos, sem geração de hooks, Zod ou mocks). Ficou em segundo lugar porque o `openapi-typescript` 7.13 declara `typescript ^5.x` como peer, o que conflita com o TypeScript 6.

### Contrato versionado (`openapi.json`)

1. O backend exporta o OpenAPI **sem precisar do banco**: `uv run python -m app.core.openapi --saida ../frontend/openapi.json` (em `backend/`).
2. O arquivo é commitado. `pnpm gerar:api` roda o Orval.
3. Na CI, um job exporta o OpenAPI de novo e falha se diferir do commitado. Mudança de contrato aparece no diff do PR.

Os `operationId` padrão do FastAPI seriam longos (`listar_documentos_v1_documentos_get`, gerando `useListarDocumentosV1DocumentosGet`). O `create_app` usa `generate_unique_id_function` com o nome da função da rota, então o Orval gera `useListarDocumentos`, `useObterDocumento` etc. Um teste garante que os nomes continuam únicos.

### Cliente HTTP e erros

```ts
// frontend/src/api/http.ts (esboço)
import { encerrarSessao, obterToken } from "@/features/auth/sessao";

export type ErroCampo = { loc: (string | number)[]; msg: string; type: string };

export class ProblemaApi extends Error {
  constructor(
    readonly status: number,
    readonly titulo: string,
    readonly detalhe: string | null,
    readonly erros: ErroCampo[] = [],
    readonly retryAfter?: number,
  ) {
    super(detalhe ?? titulo);
  }
}

export async function http<T>(url: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = obterToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const resposta = await fetch(url, { ...init, headers });
  if (resposta.status === 401 && token) encerrarSessao();
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => null);
    throw new ProblemaApi(
      resposta.status,
      corpo?.title ?? resposta.statusText,
      corpo?.detail ?? null,
      corpo?.errors ?? [],
      Number(resposta.headers.get("Retry-After")) || undefined,
    );
  }
  return (resposta.status === 204 ? undefined : await resposta.json()) as T;
}
```

A assinatura exata do mutator e o formato de retorno dos hooks com `httpClient: "fetch"` devem ser confirmados na prova de conceito.

| Status | Comportamento na interface |
|---|---|
| 401 | Limpa a sessão e vai para `/login?redirect=<rota atual>` |
| 403 | Toast "Seu perfil não permite esta ação" |
| 404 | Página "não encontrado" na rota de detalhe |
| 409 | Toast com o `detail`; na exclusão, diálogo oferecendo **Desativar** |
| 422 | `errors[].loc` (`["body", "nome"]`) → `setError("nome", …)` no formulário |
| 429 | Toast "Muitas requisições, tente em N s" usando `Retry-After`; o Query não refaz a chamada antes disso |
| 5xx / rede | Toast genérico + error boundary da rota; nada de stack trace na tela |

### Sessão e token

- O token fica **em memória**, com cópia em `sessionStorage` para sobreviver ao F5 (some ao fechar a aba). Evitar `localStorage`.
- `expires_in` (8 h) vira um horário de expiração; aviso 10 min antes e logout ao expirar. Sem refresh token, o usuário faz login de novo a cada turno.
- Ao abrir o app, `GET /v1/auth/me` valida o token salvo e carrega perfil e nome.
- Evolução recomendada (backend): cookie `httpOnly` + `SameSite=Strict`, que funciona bem porque frontend e API ficam na mesma origem. Elimina o token acessível por JavaScript.

### Casos específicos

- **Upload de PDF**: `fetch` não informa progresso de envio. Usar `XMLHttpRequest` só nessa função (`upload.onprogress`), mantendo o mesmo tratamento de erros. Validar no navegador tipo e tamanho (50 MiB) antes de enviar.
- **Status da ingestão**: `refetchInterval` condicional, parando quando o status sair de `PENDENTE`/`PROCESSANDO`:

  ```ts
  useObterDocumento(id, {
    query: {
      refetchInterval: (query) =>
        ["PENDENTE", "PROCESSANDO"].includes(query.state.data?.status_processamento ?? "") ? 3000 : false,
    },
  });
  ```

- **Agente**: a resposta pode demorar (o nginx tem `proxy_read_timeout 120s`). Botão de cancelar com `AbortController`, mensagens de etapa ("buscando trechos…", "gerando resposta…") e nenhum retry automático (cada chamada custa tokens e conta no limite de 20/min).
- **Selects com muitos registros** (família, equipamento): combobox assíncrono usando o filtro `busca` da API com debounce, já que o máximo por página é 100.

## 5. Telas

| Tela | Rotas da API | Perfil |
|---|---|---|
| Login | `POST /v1/auth/login` | público |
| Primeiro acesso (bootstrap) | `POST /v1/auth/bootstrap` (409 → vai para login) | público |
| **Assistente** (Q&A) | `POST /v1/agente/perguntar` | todos |
| Busca em documentos | `POST /v1/busca` | todos |
| Fabricantes | `/v1/fabricantes` (CRUD) | leitura: todos; escrita: ADMIN/OPERADOR |
| Famílias | `/v1/familias` (CRUD) + `/v1/tipos-equipamento` | idem |
| Equipamentos | `/v1/equipamentos` (CRUD) | idem |
| Documentos (lista, detalhe, upload, reprocessar) | `/v1/documentos`, `.../arquivo`, `.../reprocessar` | idem |
| Parâmetros | `/v1/parametros` (CRUD) | idem |
| Falhas e alarmes | `/v1/falhas` (CRUD) | idem |
| Usuários | `GET/POST/PATCH /v1/auth/usuarios`, `GET /v1/auth/usuarios/{id}` | ADMIN |
| Minha conta (trocar senha) | `GET /v1/auth/me`, `POST /v1/auth/me/senha` | todos |
| Indicador de status | `GET /ready` | todos |

### Assistente (tela principal)

- Campo de pergunta com **contexto opcional** acima: fabricante → família → equipamento, tipo de documento, idioma e firmware. O contexto escolhido fica na URL e persiste entre perguntas.
- Resposta em Markdown. As marcas `[1]`, `[2]` viram botões; ao clicar, um painel lateral mostra o trecho citado, documento, seção e página.
- Cartões para `parametros` (código, nome, unidade, mínimo/máximo/padrão) e `falhas` (tipo FALHA/ALARME com cor, causa, solução, reação).
- Rodapé discreto com `modelo_llm` e `trechos_consultados`; botão de copiar resposta.
- Histórico só no navegador (IndexedDB ou `sessionStorage`) até o backend ter histórico por usuário.
- Abrir o PDF na página citada: `GET /v1/documentos/{id}/arquivo` (com `ETag`, então o navegador não baixa de novo o mesmo manual) + visualizador `react-pdf` na `pagina` da citação.

### Catálogo, documentos, parâmetros e falhas

- Um componente `TabelaDados` (TanStack Table) com paginação no servidor, ordenação, filtros em barra e **estado na URL** (link compartilhável, por exemplo "falhas do SINAMICS G120, firmware 4.7").
- Criação e edição em painel lateral (sheet) com o formulário gerado a partir do schema Zod; `PATCH` envia só os campos alterados (`dirtyFields`), como o backend espera.
- Documentos: badge de status (`PENDENTE` cinza, `PROCESSANDO` azul animado, `INDEXADO` verde, `ERRO` vermelho com a mensagem), área de arrastar e soltar para o PDF, seleção de equipamentos filtrada pelas famílias escolhidas (regra validada no backend).
- Parâmetros e falhas podem ter centenas de linhas por família: virtualização (TanStack Virtual) e códigos em fonte monoespaçada.

Exemplo de filtros validados na URL:

```ts
// src/routes/_app/falhas.tsx
const filtros = z.object({
  id_familia: z.uuid().optional(),
  codigo: z.string().optional(),
  tipo: z.enum(["FALHA", "ALARME"]).optional(),
  versao_firmware: z.string().optional(),
  limit: z.number().int().min(1).max(100).default(20),
  offset: z.number().int().min(0).default(0),
});

export const Route = createFileRoute("/_app/falhas")({
  validateSearch: filtros,
  component: PaginaFalhas,
});
```

## 6. UX para ambiente industrial

- **Uso em campo**: tablets e notebooks no painel elétrico. Layout responsivo a partir de 768 px, alvos de toque ≥ 44 px, sem depender de hover.
- **Tema escuro e alto contraste**: ambientes com pouca luz ou reflexo; tema claro/escuro com preferência salva.
- **Códigos técnicos** (`p1120`, `F07801`, `6SL3210-1KE21-3UF1`) em fonte monoespaçada e com botão de copiar.
- **Rede restrita de fábrica**: nada de CDN em tempo de execução. Fontes (`@fontsource-variable/inter`, JetBrains Mono) e ícones vão no build.
- **Acessibilidade**: alvo WCAG 2.2 AA (Radix já entrega foco e teclado; `jsx-a11y` no lint).
- **Atalhos**: `Ctrl+K` abre uma paleta para ir direto a um parâmetro, falha ou equipamento pelo código.
- **Formatação**: `Intl.NumberFormat("pt-BR")` para potência/corrente/tensão e `Intl.DateTimeFormat("pt-BR")` para datas.
- Sem PWA/offline no início: o caso de uso em campo sem rede fica com o aplicativo Android.

## 7. Estrutura de pastas e convenções

```text
frontend/
  package.json, pnpm-lock.yaml, pnpm-workspace.yaml, .nvmrc
  vite.config.ts, tsconfig.json, eslint.config.js, .prettierrc
  orval.config.ts, openapi.json          contrato exportado do backend (commitado)
  Dockerfile, nginx.conf
  e2e/                                    Playwright
  src/
    main.tsx                              monta providers e o router
    routeTree.gen.ts                      gerado pelo plugin do TanStack Router
    app/                                  providers (Query, Router, tema, sessão)
    api/
      http.ts                             mutator: token, problem+json, 401/429
      gerado/                             saída do Orval (não editar)
    routes/                               rotas por arquivo
      __root.tsx, login.tsx, primeiro-acesso.tsx
      _app.tsx                            layout autenticado + guarda
      _app/assistente.tsx, _app/busca.tsx
      _app/catalogo/fabricantes.tsx, familias.tsx, equipamentos.tsx
      _app/documentos/index.tsx, $idDocumento.tsx
      _app/parametros.tsx, _app/falhas.tsx
      _app/admin/usuarios.tsx
    features/                             espelha os domínios do backend
      auth/, agente/, busca/, catalogo/, documentos/, parametros/, falhas/, usuarios/
    components/
      ui/                                 shadcn/ui (copiados)
      tabela-dados/, problema-alerta/, confirmar-exclusao/, status-badge/
    lib/                                  formatação (Intl), rótulos de enums, utilitários
    test/                                 setup do Vitest e servidor MSW
```

Convenções:

- **Vocabulário do domínio em português**, igual ao backend (`Fabricante`, `Familia`, `features/documentos`). Termos técnicos de React em inglês (`useQuery`, `Provider`).
- Campos da API em `snake_case` como vêm do contrato; sem mapear para `camelCase`.
- Arquivos em `kebab-case`; componentes em `PascalCase`.
- Nada dentro de `src/api/gerado/` é editado à mão.
- TypeScript `strict` + `noUncheckedIndexedAccess`; sem `any` (o lint barra).
- Imports com alias `@/` para `src/`.

## 8. Qualidade, testes e CI

| Nível | Ferramenta | O que cobre |
|---|---|---|
| Tipos | `tsc --noEmit` | Contrato gerado × uso nas telas |
| Lint | ESLint 9 (typescript-eslint com regras que usam tipos, react-hooks, jsx-a11y, plugin do TanStack Query) | Bugs comuns, hooks, acessibilidade |
| Formatação | Prettier (`--check` na CI) | Estilo |
| Unitário / componente | Vitest + Testing Library + MSW (handlers gerados pelo Orval) | Formulários, tratamento de erro, guarda de perfil, polling |
| E2E | Playwright contra o Compose com `AMBIENTE=teste` | Login → cadastro de família → documento → upload → busca → pergunta |

Job novo no `.github/workflows/ci.yml`, rodando só quando `frontend/**` ou o contrato mudar:

```yaml
frontend:
  name: Frontend
  runs-on: ubuntu-latest
  defaults:
    run:
      working-directory: frontend
  steps:
    - uses: actions/checkout@v4
    - uses: pnpm/action-setup@v4
    - uses: actions/setup-node@v4
      with:
        node-version-file: frontend/.nvmrc
        cache: pnpm
        cache-dependency-path: frontend/pnpm-lock.yaml
    - run: pnpm install --frozen-lockfile
    - run: pnpm gerar:api && git diff --exit-code src/api/gerado
    - run: pnpm typecheck
    - run: pnpm lint
    - run: pnpm format:check
    - run: pnpm test --run
    - run: pnpm build
```

O hook de pré-commit (`.pre-commit-config.yaml`) pode ganhar Prettier e ESLint para `frontend/`.

## 9. Lacunas no backend (pré-requisitos)

As lacunas de prioridade alta e média foram resolvidas na branch `feat/backend-pre-frontend`:

| Prioridade | Lacuna | Situação |
|---|---|---|
| Alta | Listagem e detalhe de usuários | Resolvida: `GET /v1/auth/usuarios` (filtros `busca`, `perfil`, `ativo`) e `GET /v1/auth/usuarios/{id}`; o último ADMIN ativo não pode ser rebaixado nem desativado (409) |
| Alta | Download do PDF | Resolvida: `GET /v1/documentos/{id}/arquivo` (`inline`, `ETag`/304). Sem `Range` e sem URL pré-assinada no S3 por enquanto |
| Alta | Exportar o OpenAPI sem banco + `operationId` limpo | Resolvida: `python -m app.core.openapi`; operationId = nome da função |
| Média | Saber se o bootstrap é necessário | Resolvida: `GET /v1/auth/bootstrap` → `{ "necessario": bool }` |
| Média | Usuário trocar a própria senha | Resolvida: `POST /v1/auth/me/senha` (204; senha atual errada → 422, não 401) |
| Média | Rate limit por usuário | Resolvida: chave pelo `sub` do JWT; sem token, por IP; rotas de autenticação sempre por IP (`RATE_LIMIT_POR_USUARIO`) |
| Média | Filtro por status de processamento | Resolvida: `GET /v1/documentos?status_processamento=ERRO` |

Continuam pendentes (prioridade baixa):

| Prioridade | Lacuna | Por que o frontend precisa |
|---|---|---|
| Baixa | Streaming da resposta do agente (SSE) | Mostrar o texto conforme é gerado |
| Baixa | Histórico de conversas por usuário (já no roadmap) e feedback da resposta | Histórico entre dispositivos; medir qualidade do agente |
| Baixa | Sessão em cookie `httpOnly` (+ refresh) | Tirar o token do alcance de JavaScript |

## 10. Build e deploy

Imagem do frontend em dois estágios:

```dockerfile
# frontend/Dockerfile
FROM node:24-alpine AS build
WORKDIR /app
RUN npm install -g pnpm@11
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

FROM nginx:1.30-alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/dist /usr/share/nginx/html
```

No nginx, o mesmo servidor entrega o SPA e encaminha a API:

```nginx
location /v1/   { proxy_pass http://api_upstream; }   # + headers já usados hoje
location = /health { proxy_pass http://api_upstream; }
location = /ready  { proxy_pass http://api_upstream; }

location /assets/ {
    root /usr/share/nginx/html;
    add_header Cache-Control "public, max-age=31536000, immutable";
}

location / {
    root /usr/share/nginx/html;
    try_files $uri /index.html;
    add_header Cache-Control "no-cache";
}
```

Também no nginx: cabeçalhos de segurança (`Content-Security-Policy` restrita a `'self'`, `X-Content-Type-Options`, `Referrer-Policy`) e manter `client_max_body_size 60m` para o upload.

Encaixe no Compose e no CD:

- O serviço `proxy` do `docker-compose.scale.yml` passa a usar a imagem do frontend (que já contém o nginx com o build), em vez de `nginx:1.27-alpine` + volume.
- Para o caso sem escala, um serviço `web` no `docker-compose.prod.yml` com a mesma imagem.
- Em produção, `CORS_ORIGINS` pode ficar vazio (mesma origem).
- O `cd.yml` ganha um segundo build/push: `ghcr.io/<org>/automacao-industrial-web`.

## 11. Ambiente local

| Item | Versão | Observação |
|---|---|---|
| Node.js | 24.22 | Nesta máquina há Node 24.5 e um `npm -v` que responde 6.14 (npm antigo no `PATH`). Instalar o 24.22 com `fnm` ou `nvm-windows` e conferir que `npm -v` mostra 11.x |
| pnpm | 11.x | `npm install -g pnpm@11`, ou campo `packageManager` no `package.json` com Corepack (ainda incluso no Node 24) |
| `.nvmrc` | `24` | Lido pela CI e pelos gerenciadores de versão |
| `engines` | `"node": ">=24.11 <25"` | Barra instalação com Node fora da linha LTS |

Fluxo do dia a dia:

```powershell
# Terminal 1 — backend (como hoje)
cd backend; uv run uvicorn app.main:create_app --factory --reload

# Terminal 2 — frontend
cd frontend
pnpm install
pnpm gerar:api     # após mudança no contrato
pnpm dev           # http://localhost:5173, proxy de /v1 para :8000
```

```ts
// frontend/vite.config.ts (trecho)
server: {
  port: 5173,
  proxy: {
    "/v1": "http://127.0.0.1:8000",
    "/health": "http://127.0.0.1:8000",
    "/ready": "http://127.0.0.1:8000",
  },
},
```

## 12. Plano de entrega

Cada fase em sua branch a partir de `development` (nunca direto nela):

| Fase | Branch sugerida | Entrega |
|---|---|---|
| 0 — Fundação | `feat/frontend-fundacao` | Projeto Vite + TS + Tailwind + shadcn/ui, ESLint/Prettier, Vitest, TanStack Router/Query, Orval com `openapi.json`, `http.ts`, layout, login, guarda por perfil, primeiro acesso (bootstrap), job de CI, Dockerfile + nginx |
| 1 — Catálogo | `feat/frontend-catalogo` | `TabelaDados` genérica, fabricantes, famílias, equipamentos, filtros na URL, exclusão com 409 → desativar |
| 2 — Documentos | `feat/frontend-documentos` | CRUD, vínculo família/equipamento, upload com progresso, polling de status, reprocessar |
| 3 — Busca e assistente | `feat/frontend-assistente` | Busca com filtros, assistente com citações e cartões de parâmetro/falha, histórico local, visualizador de PDF na página citada |
| 4 — Parâmetros e falhas | `feat/frontend-parametros-falhas` | Tabelas virtualizadas, CRUD, paleta `Ctrl+K` por código |
| 5 — Administração e produção | `feat/frontend-producao` | Usuários, minha conta (troca de senha), tema escuro, revisão de acessibilidade, E2E Playwright, Compose prod/escala e CD da imagem `web` |

Documentação a acompanhar: `docs/22-frontend.md` (como rodar, estrutura, convenções) e regras do assistente em `.cursor/rules/` para o frontend (stack e versões, como já existe para o backend).

## 13. Decisões em aberto

| Decisão | Recomendação | Alternativa |
|---|---|---|
| Gerador do cliente | Orval 8 (hooks + Zod + mocks) | `openapi-typescript` + `openapi-fetch` (mais enxuto; peer de TS 5) |
| Vite | 8.3 | 7.3 (se a prova de conceito mostrar problema com Rolldown) |
| Idioma da interface | Só pt-BR, textos centralizados | i18next desde o início |
| Identidade visual | Tokens do shadcn/ui ajustados à marca | Design system próprio |
| Sessão | Token em memória + `sessionStorage` | Cookie `httpOnly` (exige mudança no backend) |
| Hospedagem do frontend | Mesmo nginx da API (mesma origem) | CDN/hosting estático separado (exige CORS e domínio próprio) |
