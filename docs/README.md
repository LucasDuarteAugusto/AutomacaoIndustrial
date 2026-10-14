# Documentação — AutomacaoIndustrial

Backend em FastAPI + PostgreSQL/pgvector para apoiar profissionais de automação industrial no comissionamento de acionamentos de motores (relés de gerenciamento como o SIMOCODE, soft starters e inversores de frequência), com busca semântica sobre a documentação técnica dos fabricantes.

## Índice

| Documento | Conteúdo |
|---|---|
| [01 — Rodando localmente](01-rodando-localmente.md) | Pré-requisitos, primeira execução, comandos do dia a dia e solução de problemas |
| [02 — Banco de dados](02-banco-de-dados.md) | Diagrama, tabelas, colunas, restrições e convenções de nomes |
| [03 — Migrations](03-migrations.md) | Como criar, revisar, aplicar e desfazer mudanças no schema com Alembic |
| [04 — Arquitetura](04-arquitetura.md) | Stack, camadas, estrutura de pastas e decisões técnicas |
| [05 — API](05-api.md) | Rotas, paginação, filtros, formato de erros e exemplos |
| [06 — Testes](06-testes.md) | Como os testes funcionam, como rodar e como escrever novos |
| [07 — Domínio de acionamentos](07-dominio-acionamentos.md) | Glossário técnico (SIMOCODE, soft starter, inversor) e como isso vira dado |
| [08 — Roadmap](08-roadmap.md) | Fases do projeto e próximos passos |

## Resumo rápido

```powershell
docker compose up -d --wait
uv run alembic upgrade head
uv run uvicorn app.main:create_app --factory --reload
```

Documentação interativa da API: <http://127.0.0.1:8000/docs>
