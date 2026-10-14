# 07 — Domínio: acionamento de motores

Glossário para quem desenvolve o sistema e ponte entre o vocabulário de campo e o modelo de dados.

## Os três tipos de equipamento iniciais

### Relé de gerenciamento de motor (`RELE_GERENCIAMENTO`)

Exemplo: **Siemens SIMOCODE pro** (C, S, V).

- **Não aciona** o motor sozinho: comanda o contator e **protege e monitora**.
- Funções: proteção térmica (sobrecarga), falta de fase, desbalanço, medição de corrente/tensão/potência, contagem de partidas e horas.
- Implementa a **lógica de partida** (direta, reversora, estrela-triângulo, Dahlander) por blocos de função configuráveis.
- Comunica com o CLP por **PROFIBUS DP**, **PROFINET**, Modbus RTU ou EtherNet/IP.
- Configurado por software (SIMOCODE ES, no TIA Portal).
- Documentos típicos: manual do sistema, descrição dos blocos de função, manual de comunicação, lista de diagnósticos.

### Soft starter (`SOFT_STARTER`)

Exemplos: Siemens **SIRIUS 3RW30/3RW40/3RW44/3RW5x**, WEG **SSW**, ABB **PSTX**.

- Controla a **tensão** aplicada ao motor na partida e na parada usando tiristores (SCR).
- Reduz **pico de corrente** e **golpe mecânico** (correias, acoplamentos, golpe de aríete em bombas).
- **Não controla velocidade** em regime: após a rampa, normalmente fecha um **contator de bypass**.
- Parâmetros típicos: tensão inicial, tempo de rampa de partida/parada, limite de corrente, classe de disparo térmico, modo de parada de bomba.

### Inversor de frequência (`INVERSOR`)

Exemplos: Siemens **SINAMICS G120/G120C/G120X/V20**, WEG **CFW500/CFW11**, Danfoss **FC 302**, ABB **ACS580**.

- Retifica a rede, mantém um **barramento CC** e gera tensão/frequência variáveis (PWM) para controlar **velocidade e torque**.
- Modos de controle: **escalar (V/f)** — simples, bombas e ventiladores; **vetorial** (sem ou com encoder) — torque alto em baixa rotação.
- Comissionamento típico: dados de placa do motor, **identificação/autotuning**, rampas, limites, fonte de comando e de referência, E/S digitais e analógicas, comunicação, funções de segurança (STO).
- Parâmetros identificados por código: `p1120` (tempo de rampa de aceleração no SINAMICS), `P0100` (WEG CFW). Falhas e alarmes também: `F07801` (sobrecorrente no SINAMICS).
- Documentos típicos: guia rápido, manual de operação, **lista de parâmetros** (centenas de páginas), manual de comunicação, manual de segurança funcional.

## Vocabulário

| Termo | Significado |
|---|---|
| Comissionamento | Colocar o equipamento em operação: parametrizar, testar, ajustar e documentar |
| Dados de placa | Potência, tensão, corrente, frequência, rotação e cos φ do motor (placa de identificação) |
| Código de pedido / MLFB | Código único do produto no fabricante (ex.: `6SL3210-1KE21-3UF1`). No sistema: `EQUIPAMENTOS.CODIGO_PEDIDO` |
| Família / série | Linha de produto que compartilha manuais e parâmetros (ex.: SINAMICS G120). No sistema: `FAMILIAS` |
| Firmware | Software interno do equipamento; parâmetros mudam entre versões. No sistema: `DOCUMENTOS.VERSAO_FIRMWARE` |
| Rampa | Tempo para acelerar/desacelerar entre zero e a velocidade/tensão nominal |
| Bypass | Contator que curto-circuita o soft starter após a partida |
| STO (Safe Torque Off) | Função de segurança que remove o torque do motor de forma certificada |
| PROFINET / PROFIBUS | Redes industriais da Siemens/PI para comunicação com CLP |
| Telegrama | Estrutura padrão de dados trocados entre CLP e inversor (ex.: telegrama 1, 20, 352) |
| Falha (fault) / Alarme (warning) | Falha desliga o acionamento; alarme só avisa |

## Do mundo real para o modelo de dados

| Pergunta de campo | Onde a resposta está | Como o sistema vai encontrar |
|---|---|---|
| "Qual parâmetro ajusta a rampa de aceleração no G120?" | Lista de parâmetros da família | Filtro por família + busca semântica nos trechos (fase 2) ou tabela `PARAMETROS` (fase 3) |
| "O que significa F07801?" | Lista de falhas do manual | Busca textual exata pelo código + tabela `FALHAS` (fase 3) |
| "Como ligo o SIMOCODE na PROFINET?" | Manual de comunicação | Filtro `tipo_documento=MANUAL_COMUNICACAO` + busca semântica |
| "Qual a corrente nominal do 6SL3210-1KE21-3UF1?" | Datasheet do modelo | `EQUIPAMENTOS.CORRENTE_NOMINAL_A` ou documento ligado ao modelo |

## Por que a estrutura do documento importa para a IA

Manuais misturam texto corrido, **tabelas de parâmetros**, **tabelas de falhas**, procedimentos passo a passo e diagramas. Na ingestão (fase 2), o documento será dividido em trechos respeitando seções e tipo de conteúdo. Uma tabela de falhas cortada ao meio, ou um parâmetro separado da sua descrição, gera respostas erradas com aparência de certeza. Por isso cada trecho guardará seção, página e tipo de conteúdo, além da ligação com família, modelo, idioma e firmware.
