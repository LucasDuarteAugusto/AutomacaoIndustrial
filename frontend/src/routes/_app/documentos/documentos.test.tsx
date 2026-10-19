import { act, screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";

import { documento, entrarComo, ID_DOCUMENTO } from "@/test/dados";
import { servidor } from "@/test/servidor";
import { renderizarApp } from "@/test/utils";

describe("Documentos", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("lista aplica os filtros da URL na consulta", async () => {
    entrarComo("OPERADOR");
    let parametros: URLSearchParams | undefined;
    servidor.use(
      http.get("*/v1/documentos", ({ request }) => {
        parametros = new URL(request.url).searchParams;
        return HttpResponse.json({
          items: [documento({ status_processamento: "ERRO", erro_processamento: "Voyage indisponível" })],
          total: 1,
        });
      }),
    );
    renderizarApp("/documentos?status_processamento=ERRO&busca=G120");

    expect(
      await screen.findByRole("link", { name: "SINAMICS G120 - Lista de parâmetros" }),
    ).toBeInTheDocument();
    expect(parametros?.get("status_processamento")).toBe("ERRO");
    expect(parametros?.get("busca")).toBe("G120");
    expect(parametros?.get("limit")).toBe("20");
    expect(screen.getByRole("button", { name: /Novo documento/ })).toBeInTheDocument();
    expect(within(screen.getByRole("table")).getByText("Erro")).toBeInTheDocument();
  });

  it("perfil LEITURA não vê ações de escrita", async () => {
    entrarComo("LEITURA");
    servidor.use(
      http.get("*/v1/documentos", () => HttpResponse.json({ items: [documento()], total: 1 })),
      http.get(`*/v1/documentos/${ID_DOCUMENTO}`, () => HttpResponse.json(documento())),
    );
    const { usuario } = renderizarApp("/documentos");

    await usuario.click(await screen.findByRole("link", { name: "SINAMICS G120 - Lista de parâmetros" }));

    expect(await screen.findByRole("button", { name: /Visualizar PDF/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Excluir/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Reprocessar/ })).not.toBeInTheDocument();
    expect(screen.queryByText(/Arraste o PDF aqui/)).not.toBeInTheDocument();
  });

  it("atualiza o status enquanto indexa e para ao chegar em INDEXADO", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    entrarComo("ADMIN");
    const respostas = [
      documento({ status_processamento: "PROCESSANDO", paginas: null }),
      documento({ status_processamento: "INDEXADO" }),
    ];
    let chamadas = 0;
    servidor.use(
      http.get(`*/v1/documentos/${ID_DOCUMENTO}`, () => {
        const atual = respostas[Math.min(chamadas, respostas.length - 1)];
        chamadas += 1;
        return HttpResponse.json(atual);
      }),
    );
    renderizarApp(`/documentos/${ID_DOCUMENTO}`);

    expect(await screen.findByText(/Indexando o PDF/)).toBeInTheDocument();
    await act(() => vi.advanceTimersByTimeAsync(3500));
    expect(await screen.findByText("Indexado", { selector: "[data-slot=badge]" })).toBeInTheDocument();
    expect(screen.getByText(/Arraste o PDF aqui/)).toBeInTheDocument();

    const depoisDeIndexar = chamadas;
    await act(() => vi.advanceTimersByTimeAsync(10_000));
    expect(chamadas).toBe(depoisDeIndexar);
  });
});
