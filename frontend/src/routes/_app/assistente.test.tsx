import { screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import type { AgentePerguntaRequest, AgenteRespostaOut } from "@/api/gerado/modelos";
import { entrarComo } from "@/test/dados";
import { servidor } from "@/test/servidor";
import { renderizarApp } from "@/test/utils";

const ID_FAMILIA = "22222222-2222-4222-8222-222222222222";

const RESPOSTA: AgenteRespostaOut = {
  pergunta: "O que é F07801?",
  resposta: "A falha [F1] indica sobrecorrente. Ajuste a rampa em [P1] conforme o manual [1].",
  citacoes: [
    {
      indice: 1,
      id_trecho: "33333333-3333-4333-8333-333333333333",
      id_documento: "11111111-1111-4111-8111-111111111111",
      titulo_documento: "SINAMICS G120 - Manual de operação",
      codigo_documento: null,
      secao: "Falhas e alarmes",
      pagina: 214,
      trecho: "F07801 Sobrecorrente no motor. Verificar rampas e dados do motor.",
      score: 0.032,
    },
  ],
  parametros: [
    {
      id_parametro: "44444444-4444-4444-8444-444444444444",
      id_familia: ID_FAMILIA,
      versao_firmware: null,
      codigo: "p1120",
      nome: "Tempo de aceleração",
      descricao: "Tempo para acelerar de 0 até a frequência máxima.",
      unidade: "s",
      valor_min: 0,
      valor_max: 999999,
      valor_padrao: "10",
      grupo: "Rampas",
      somente_leitura: false,
      idioma: "pt-BR",
      id_documento: null,
      pagina: null,
      ativo: true,
      created_at: "2026-10-01T12:00:00Z",
      updated_at: "2026-10-01T12:00:00Z",
    },
  ],
  falhas: [
    {
      id_falha: "55555555-5555-4555-8555-555555555555",
      id_familia: ID_FAMILIA,
      versao_firmware: null,
      codigo: "F07801",
      tipo: "FALHA",
      titulo: "Sobrecorrente no motor",
      descricao: null,
      causa: "Rampa de aceleração curta demais.",
      solucao: "Aumentar p1120.",
      reacao: "OFF2",
      idioma: "pt-BR",
      id_documento: null,
      pagina: null,
      ativo: true,
      created_at: "2026-10-01T12:00:00Z",
      updated_at: "2026-10-01T12:00:00Z",
    },
  ],
  modelo_llm: "gpt-5-mini",
  trechos_consultados: 1,
};

describe("Assistente", () => {
  it("envia a pergunta com o contexto da URL e mostra resposta, cartões e fonte", async () => {
    entrarComo("LEITURA");
    let corpo: AgentePerguntaRequest | undefined;
    servidor.use(
      http.get(`*/v1/familias/${ID_FAMILIA}`, () =>
        HttpResponse.json({
          id_familia: ID_FAMILIA,
          id_fabricante: "66666666-6666-4666-8666-666666666666",
          id_tipo_equipamento: "77777777-7777-4777-8777-777777777777",
          nome: "SINAMICS G120",
          descricao: null,
          ativo: true,
          created_at: "2026-10-01T12:00:00Z",
          updated_at: "2026-10-01T12:00:00Z",
        }),
      ),
      http.post("*/v1/agente/perguntar", async ({ request }) => {
        corpo = (await request.json()) as AgentePerguntaRequest;
        return HttpResponse.json(RESPOSTA);
      }),
    );
    const { usuario } = renderizarApp(`/assistente?id_familia=${ID_FAMILIA}`);

    await usuario.type(await screen.findByLabelText("Pergunta"), "O que é F07801?");
    await usuario.click(screen.getByRole("button", { name: /Perguntar/ }));

    expect(await screen.findByText(/indica sobrecorrente/)).toBeInTheDocument();
    expect(corpo).toMatchObject({ pergunta: "O que é F07801?", id_familia: ID_FAMILIA, id_fabricante: null });

    const parametros = screen.getByRole("region", { name: "Parâmetros encontrados" });
    expect(within(parametros).getByText("p1120")).toBeInTheDocument();
    const falhas = screen.getByRole("region", { name: "Falhas e alarmes encontrados" });
    expect(within(falhas).getByText("Aumentar p1120.")).toBeInTheDocument();

    await usuario.click(screen.getByRole("button", { name: "Ver fonte 1" }));
    const painel = await screen.findByRole("dialog");
    expect(within(painel).getByText(/Sobrecorrente no motor\. Verificar rampas/)).toBeInTheDocument();
    expect(within(painel).getByRole("button", { name: "Abrir PDF na página 214" })).toBeInTheDocument();
  });

  it("429 bloqueia novas perguntas e mostra a contagem", async () => {
    entrarComo();
    servidor.use(
      http.post("*/v1/agente/perguntar", () =>
        HttpResponse.json(
          { title: "Limite de requisições excedido", status: 429, detail: "Limite excedido." },
          { status: 429, headers: { "Retry-After": "30" } },
        ),
      ),
    );
    const { usuario } = renderizarApp("/assistente");

    await usuario.type(await screen.findByLabelText("Pergunta"), "Qual o padrão do p1120?");
    await usuario.click(screen.getByRole("button", { name: /Perguntar/ }));

    expect(await screen.findByText(/Tente de novo em 30s/)).toBeInTheDocument();
    expect(screen.getByText("Muitas requisições. Tente novamente em 30 s.")).toBeInTheDocument();
    await usuario.type(screen.getByLabelText("Pergunta"), "outra");
    expect(screen.getByRole("button", { name: "Perguntar" })).toBeDisabled();
  });
});
