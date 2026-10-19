# 22 — Frontend (React)

SPA em `frontend/` que consome a API pelo contrato OpenAPI. Decisões e alternativas: [21 — Estudo do frontend React](21-estudo-frontend-react.md).

## Telas desta entrega

| Rota | Tela | Perfil |
|---|---|---|
| `/login` | Login (redireciona para o primeiro acesso se a base estiver vazia) | público |
| `/primeiro-acesso` | Criação do primeiro ADMIN (`POST /v1/auth/bootstrap`) | público |
| `/assistente` | Perguntas ao agente com contexto na URL, citações clicáveis, cartões de parâmetros/falhas, PDF na página citada | todos |
| `/busca` | Busca híbrida com consulta e filtros na URL, trechos realçados, PDF na página | todos |
| `/documentos` | Lista paginada com filtros (título/código, tipo, status, idioma, família) e cadastro | leitura: todos; escrita: ADMIN/OPERADOR |
| `/documentos/:id` | Metadados, upload do PDF com progresso, status da indexação (atualiza sozinho), reprocessar, excluir, visualizar PDF | idem |
| menu do usuário | Minha conta (troca de senha), tema claro/escuro, sair | todos |

Catálogo (CRUD de fabricantes, famílias e equipamentos), parâmetros, falhas e usuários ficam para a próxima entrega. As telas atuais só leem o catálogo, para os filtros.

## Rodando localmente

Pré-requisitos: **Node.js 24** e **pnpm 11** (via Corepack). O backend precisa estar no ar em `http://127.0.0.1:8000` ([01 — Rodando localmente](01-rodando-localmente.md)).

```powershell
# Node 24 (com nvm-windows: nvm install 24 ; nvm use 24)
node -v                # v24.x
corepack enable pnpm   # usa a versão de "packageManager" do package.json

cd frontend
pnpm install
pnpm dev               # http://localhost:5173
```

O Vite encaminha `/v1`, `/health` e `/ready` para a API (`vite.config.ts`), então o código sempre usa caminhos relativos e não depende de CORS.

| Comando | O que faz |
|---|---|
| `pnpm dev` | Servidor de desenvolvimento com recarga |
| `pnpm build` | `tsc -b` + build de produção em `dist/` |
| `pnpm typecheck` | Checagem de tipos |
| `pnpm lint` | ESLint (regras que usam tipos, hooks, TanStack Query) |
| `pnpm format` / `format:check` | Prettier (com ordenação de classes Tailwind) |
| `pnpm test` | Vitest (modo watch; `--run` para rodar uma vez) |
| `pnpm contrato:atualizar` | Exporta o OpenAPI do backend e regenera o cliente |

## Contrato com o backend

```text
Pydantic (backend) ──► openapi.json ──► Orval ──► src/api/gerado/
                         (versionado)              ├─ hooks TanStack Query (useListarDocumentos, usePerguntar, …)
                                                   ├─ modelos TypeScript
                                                   ├─ schemas Zod (limites do Pydantic → formulários)
                                                   └─ handlers MSW (testes)
```

1. Mudou rota ou schema no backend? Rode `pnpm contrato:atualizar` (usa `uv run python -m app.core.openapi`, sem banco).
2. Commite `openapi.json` e `src/api/gerado/` junto com a mudança.
3. A CI regenera e falha se houver diferença.

Nada em `src/api/gerado/` é editado à mão. O cliente HTTP (`src/api/http.ts`) é o *mutator* do Orval:
- injeta o Bearer;
- converte erros `application/problem+json` em `ProblemaApi`;
- encerra a sessão em 401.

O upload usa `XMLHttpRequest` (`src/api/upload.ts`), porque o `fetch` não informa o progresso de envio.

## Sessão e perfis

- O token fica em memória, com cópia em `sessionStorage`. Fechar a aba encerra a sessão.
- Validade de 8 h (um turno). O app avisa 10 min antes e manda para o login ao expirar.
- Na entrada de qualquer rota autenticada, `GET /v1/auth/me` confirma o token e atualiza o perfil.
- `LEITURA` não vê botões de escrita. O backend continua sendo quem bloqueia (403).

| Erro da API | Interface |
|---|---|
| 401 | Limpa a sessão e vai para `/login?redirect=<rota>` |
| 403 | "Seu perfil não permite esta ação." |
| 409 | Mensagem do `detail` (ex.: arquivo duplicado) |
| 422 | Erros por campo no formulário (`errors[].loc`) |
| 429 | Aviso com contagem regressiva do `Retry-After`; o assistente bloqueia novas perguntas |
| rede / 5xx | Alerta com "Tentar de novo" |

## Estrutura

```text
frontend/
  openapi.json, orval.config.ts     contrato e geração do cliente
  vite.config.ts                    proxy da API, plugin de rotas, Vitest
  Dockerfile, nginx/                imagem de produção (SPA + proxy /v1)
  src/
    main.tsx, app/                  providers, QueryClient, router
    routes/                         rotas por arquivo (TanStack Router)
    api/                            http.ts, problema.ts, upload.ts, gerado/
    features/                       auth, layout, agente, busca, contexto, catalogo, documentos
    components/                     ui/ (shadcn) + compartilhados (tabela, combobox, PDF, markdown…)
    lib/                            rótulos pt-BR, formatação Intl, citações, tema
    test/                           setup, servidor MSW, dados e helper renderizarApp
```

Convenções:
- vocabulário do domínio em português, como no backend;
- campos da API em `snake_case`, como vêm do contrato;
- arquivos em `kebab-case`;
- filtros e paginação na URL (`validateSearch` com Zod), para os links poderem ser compartilhados.

## Testes

Vitest + Testing Library + MSW. Os testes de rota renderizam o app inteiro (`renderizarApp`), com guarda, providers e histórico em memória.

| Arquivo | Cobre |
|---|---|
| `src/api/http.test.ts` | Bearer, 204, 401 (com e sem token), 403, 409, 422, 429, falha de rede |
| `src/features/auth/sessao.test.ts` | Sessão, expiração, perfis, redirect seguro |
| `src/lib/citacoes.test.ts` | Marcas `[1]`, `[P1]`, `[F1]`, listas |
| `src/routes/auth.test.tsx` | Guarda com destino, primeiro acesso, login ok/errado, validação |
| `src/routes/_app/assistente.test.tsx` | Contexto da URL na requisição, resposta, cartões, painel da fonte, 429 |
| `src/routes/_app/documentos/documentos.test.tsx` | Filtros da URL, ações ocultas para LEITURA, polling até INDEXADO |

E2E com Playwright fica para a próxima fase. Com `AMBIENTE=teste` a API usa embedding e LLM falsos, o que permite rodar o fluxo completo sem chaves.

## Produção

A imagem `frontend/Dockerfile` (build em `node:24-alpine`, entrega em `nginx:1.30-alpine`):

- serve o SPA com fallback para `index.html` (sem cache) e `/assets/` com cache imutável;
- faz proxy de `/v1/`, `/health` e `/ready` para `api:8000` (mesma origem, sem CORS);
- envia CSP restrita a `'self'`, `X-Frame-Options`, `nosniff` e `Referrer-Policy`;
- mantém `client_max_body_size 60m` para o upload de PDF e expõe `/healthz`.

```powershell
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d --build
# SPA em http://localhost:8080 (WEB_PORT)
```

O CD publica `ghcr.io/<org>/automacao-industrial-web` junto com a imagem da API. O `docker-compose.scale.yml` (nginx na frente de N réplicas) ainda usa o proxy próprio; unificar com a imagem `web` fica para a próxima fase.

## Desvios em relação ao estudo

| Item | Estudo | Implementado | Motivo |
|---|---|---|---|
| ESLint | 9.39 | **10** | O ESLint 9 passou a ser marcado como sem suporte no npm (deprecated) |
| `eslint-plugin-jsx-a11y` | incluído | **removido** | Sem atualização desde out/2024 e sem suporte declarado ao ESLint 10; acessibilidade coberta por Radix + testes por papel (role) |
| `lucide-react` | 1.59 | 1.55 | O `minimumReleaseAge` (7 dias) recusou a 1.59 |
| Orval | 8.43 | 8.41 | Idem |
