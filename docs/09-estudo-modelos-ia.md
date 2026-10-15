# 09 — Estudo de modelos de IA (embedding e LLM)

Estudo de custo-benefício feito em outubro/2026 para escolher os modelos da fase 2 (busca semântica) e da fase 4 (agente). Preços são de lista e mudam com frequência: confira as páginas oficiais antes de decidir.

## Resumo

- O **custo do embedding é desprezível** neste projeto: indexar uma biblioteca grande de manuais custa de US$ 0 a ~US$ 16, uma única vez.
- O **custo recorrente é o LLM** que escreve as respostas, e ele pode ser trocado a qualquer momento por configuração, sem reindexar.
- **Decisão inicial (out/2026):**
  - **Embedding:** Voyage `voyage-context-4` (`vector(1024)`, 200M tokens grátis).
  - **LLM:** OpenAI **GPT-5 mini** (fase 4; ~US$ 2,50 por 1.000 perguntas no cenário estimado).
- Evolução depois, se o teste com manuais reais pedir: **Perplexity `pplx-embed-context-v1-4b`** (texto; pesos abertos) ou **Google `gemini-embedding-2`** (multimodal: texto e imagens). LLM mais forte sob demanda: GPT-5 ou Claude Sonnet.

## Dois modelos, duas escolhas

| | Modelo de embedding | LLM (modelo de linguagem) |
|---|---|---|
| O que faz | Transforma texto (ou imagem) em vetor para a busca por proximidade semântica | Lê os trechos encontrados e escreve a resposta |
| Quando roda | Uma vez por trecho na indexação e uma vez por pergunta | A cada pergunta, com milhares de tokens de contexto |
| Trocar depois | Exige reindexar todos os trechos | Basta mudar a configuração |
| Quando decidir | Fase 2 (define a coluna `vector(N)`) | Fase 4 |

### Situação de cada fornecedor citado

- **OpenAI**: `text-embedding-3-small` e `-large`, de jan/2024 e sem atualização. Baratos, mas são os mais fracos em recuperação multilíngue desta lista.
- **Claude (Anthropic)**: não tem modelo de embedding. A Anthropic [recomenda a Voyage AI](https://platform.claude.com/docs/en/build-with-claude/embeddings). O Claude entra como LLM.
- **Grok (xAI)**: a API expõe só um embedding antigo (`v1`, versão 0.1.0), sem benchmark publicado. Não recomendado. O Grok entra apenas como LLM, e é caro para RAG.
- **Perplexity**: o produto conhecido (Sonar) é um LLM que pesquisa na **web**, o que não ajuda a buscar nos nossos PDFs. Mas a Perplexity tem uma família própria de embeddings, a [`pplx-embed`](https://docs.perplexity.ai/docs/embeddings/quickstart), entre as melhores do mercado e com pesos abertos. O Sonar pode virar, no futuro, uma ferramenta do agente para buscar na web.
- **Gemini (Google)**: `gemini-embedding-2` é forte em multilíngue e é o principal modelo **multimodal** (texto, imagem, PDF, áudio e vídeo no mesmo espaço vetorial).

## Comparativo de embeddings

Cenário de custo: 300 documentos × 400 páginas × ~600 tokens/página, com sobreposição entre trechos ≈ **80 milhões de tokens**.

Qualidade: MTEB Multilingual v2, recuperação, nDCG@10 ([SOTA2](https://www.sota2.com/research/sota/multilingual-retrieval-on-mteb-multilingual-v2)). Quanto maior, melhor. Os números vêm de fontes diferentes e servem de referência, não de garantia.

| Modelo | Fornecedor | US$/1M tokens | Indexar 80M | Qualidade | Dimensões | Imagens | Pesos abertos |
|---|---|---|---|---|---|---|---|
| `pplx-embed-v1-4b` | Perplexity | 0,03 | US$ 2,40 | **69,7** | 2560 (reduzível) | Não | Sim |
| `pplx-embed-context-v1-4b` | Perplexity | 0,05 | US$ 4,00 | ~69,7 | 2560 (reduzível) | Não | Sim |
| `pplx-embed-v1-0.6b` | Perplexity | 0,004 | US$ 0,32 | 65,4 | 1024 | Não | Sim |
| `qwen3-embedding-8b` | Alibaba (via OpenRouter) | 0,01 | US$ 0,80 | **70,9** | 4096 (reduzível) | Não | Sim |
| `gemini-embedding-2` | Google | 0,20 (lote: 0,10) | US$ 16 (lote: US$ 8) | ~67,7 | 3072 (reduzível) | **Sim** | Não |
| `voyage-4` / `voyage-context-4` | Voyage AI | 0,06 / 0,12 | US$ 0 (200M grátis) | ~66 | 1024 | Não | Não |
| `voyage-4-large` | Voyage AI | 0,12 | US$ 0 (200M grátis) | ~66 | 1024 | Não | Não |
| `embed-v4.0` | Cohere | 0,12 | US$ 9,60 | ~61 | 1536 | Sim | Não |
| `mistral-embed` | Mistral | 0,10 | US$ 8,00 | ~63 | 1024 | Não | Não |
| `text-embedding-3-small` | OpenAI | 0,02 (lote: 0,01) | US$ 1,60 | — | 1536 | Não | Não |
| `text-embedding-3-large` | OpenAI | 0,13 | US$ 10,40 | 59,3 | 3072 | Não | Não |
| `v1` | xAI | ~0,10 | ~US$ 8 | sem dados | — | Não | Não |

Os 200M tokens grátis da Voyage são compartilhados entre os modelos `voyage-4*` da mesma conta.

## Perplexity × Gemini: texto ou imagens?

Os modelos `pplx-embed` são **só texto**. O `gemini-embedding-2` aceita texto e imagens no mesmo espaço vetorial: uma pergunta em texto ("esquema de ligação do contator de bypass do 3RW52") pode encontrar diretamente a **imagem** de um diagrama.

O Gemini é mais caro **também para texto**: US$ 0,20/1M contra US$ 0,05/1M do `pplx-embed-context-v1-4b` (4×) ou US$ 0,03/1M do `pplx-embed-v1-4b` (~7×). Isso vale mesmo que nenhuma imagem seja enviada: o preço maior é do modelo (maior, fechado e multimodal), não do uso de imagens. Imagens são cobradas à parte.

Em valores absolutos a diferença é pequena (US$ 4 contra US$ 16 para a biblioteca inteira), então o preço não decide. O que decide:

| Critério | Perplexity `pplx-embed-context-v1-4b` | Google `gemini-embedding-2` |
|---|---|---|
| Qualidade em texto PT/EN | Ligeiramente melhor | Muito boa |
| Trechos com contexto do documento | Sim (versão *context*) | Não nativamente |
| Busca em diagramas e imagens | Não | Sim |
| Dependência de fornecedor | Baixa: pesos abertos, dá para rodar localmente com os mesmos vetores | Alta: trocar exige reindexar |
| Privacidade | API paga | No plano gratuito os dados podem ser usados pelo Google; no pago, não |

### Quanto as imagens importam nos manuais?

- **Listas de parâmetros e tabelas de falhas** (o conteúdo mais consultado no comissionamento) são texto e tabela no PDF. Um modelo só de texto atende bem.
- **Diagramas de ligação, telas de IHM e curvas** são imagens. Aqui um modelo multimodal ajuda.
- **PDFs escaneados** não têm texto extraível: precisam de OCR, ou de um modelo multimodal.

### Alternativa sem trocar de modelo

Manter o texto no Perplexity e tratar as imagens com um **LLM com visão** (Gemini Flash, Claude Haiku, GPT-5 mini) que gera uma **descrição em texto** de cada figura ("Diagrama de ligação do SIRIUS 3RW52 com contator de bypass externo, bornes 1/L1..."). Essa descrição é indexada como um trecho comum, ligado à página e à imagem original.

Vantagens: um único espaço vetorial de texto, descrições pesquisáveis também pela busca textual (`tsvector`), e o agente pode citar a figura. Custo: alguns centavos a poucos dólares para milhares de figuras.

## Custo do LLM (fase 4)

Estimativa por pergunta: ~6.000 tokens de entrada (trechos + instruções) e ~500 de saída.

| Modelo | Entrada / saída (US$/1M) | Custo por 1.000 perguntas | Perfil |
|---|---|---|---|
| GPT-5 nano | 0,05 / 0,40 | ~US$ 0,50 | Muito barato; respostas simples |
| Gemini 2.5 Flash-Lite | 0,10 / 0,40 | ~US$ 0,80 | Muito barato |
| Claude Haiku 5.5 | 0,10 / 0,50 | ~US$ 0,85 | Barato e bom com texto técnico |
| GPT-5 mini | 0,25 / 2,00 | ~US$ 2,50 | Bom equilíbrio |
| Gemini 3.8 Flash | 0,75 / 3,75 | ~US$ 6,40 | Preço dobra em jan/2027 |
| Grok 4.7 | 2,00 / 6,00 | ~US$ 15 | Caro para RAG |
| Claude Sonnet 5.5 | 2,00 / 10,00 | ~US$ 17 | Alta qualidade, perguntas difíceis |

Estratégia sugerida: um modelo barato por padrão e um modelo forte só para perguntas complexas.

## Restrições técnicas no pgvector

- O índice **HNSW** aceita até **2.000 dimensões** no tipo `vector` (até 4.000 em `halfvec`).
- Modelos de 2560, 3072 ou 4096 dimensões são reduzidos via Matryoshka (o próprio fornecedor devolve menos dimensões com pouca perda).
- Alvo: **`vector(1024)`**. 160 mil trechos × 1024 dimensões ≈ 650 MB.
- O `pplx-embed` devolve vetores `int8` ou binários em base64 por padrão; o cliente decodifica para `float` antes de gravar.

## Recomendação

1. **Início (mais viável agora):** Voyage `voyage-context-4` em 1024 dimensões. Qualidade ~66 (competitiva frente a 59–71 da tabela), embedding contextualizado (bom para manuais), dimensão já alinhada ao alvo do pgvector, e 200M tokens grátis por conta — o suficiente para indexar a biblioteca e validar a fase 2 sem custo. A Anthropic indica a Voyage como provedor de embedding.
2. **Imagens:** descrições geradas por LLM com visão, indexadas como trechos de texto (independente do embedding escolhido).
3. **Se o recall no teste com manuais reais ficar abaixo do esperado:** Perplexity `pplx-embed-context-v1-4b` (~US$ 4, pesos abertos, qualidade um pouco acima).
4. **Se a busca direta em diagramas for crítica:** `gemini-embedding-2` em 1024 dimensões (~US$ 8–16).
5. **LLM** (fase 4): **GPT-5 mini** por padrão; GPT-5 ou Claude Sonnet para perguntas complexas.

### Por que ~66 não é “ruim”

Na tabela, o pior da faixa útil fica em ~59 (OpenAI large) e o topo em ~70–71. A Voyage está no meio-alto. Em RAG o que mais costuma melhorar o resultado não é subir 3 pontos no MTEB, e sim o *chunking*, o embedding contextualizado, a busca híbrida (vetor + `tsvector`) e o LLM que responde. Começar com Voyage de graça e medir com perguntas reais é a ordem certa; trocar o modelo depois é só reindexar.

## Validação antes da decisão final

1. Separar 2 ou 3 manuais reais (ex.: lista de parâmetros do SINAMICS G120 e manual do SIRIUS 3RW5x).
2. Escrever 30 a 50 perguntas de campo, anotando a página da resposta. Incluir perguntas cuja resposta está em diagramas.
3. Indexar com os candidatos (custo total abaixo de US$ 1).
4. Medir em quantas perguntas o trecho certo aparece entre os 5 primeiros resultados (recall@5).

A interface `ProvedorEmbedding` da fase 2 deixa o modelo configurável, então o teste reaproveita o código de produção.
