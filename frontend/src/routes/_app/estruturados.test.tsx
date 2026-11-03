import { screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import type { FalhaOut, FamiliaOut, ParametroOut } from "@/api/gerado/modelos";
import { entrarComo, usuario } from "@/test/dados";
import { servidor } from "@/test/servidor";
import { renderizarApp } from "@/test/utils";

const ID_FAMILIA = "cccccccc-cccc-4ccc-8ccc-cccccccccccc";

function familia(parcial: Partial<FamiliaOut> = {}): FamiliaOut {
  return {
    id_familia: ID_FAMILIA,
    id_fabricante: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    id_tipo_equipamento: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
    nome: "SINAMICS G120",
    descricao: null,
    ativo: true,
    created_at: "2026-10-03T12:00:00Z",
    updated_at: "2026-10-04T12:00:00Z",
    ...parcial,
  };
}

function parametro(parcial: Partial<ParametroOut> = {}): ParametroOut {
  return {
    id_parametro: "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
    id_familia: ID_FAMILIA,
    versao_firmware: "4.7 SP14",
    codigo: "P0305",
    nome: "Corrente nominal",
    descricao: "Corrente nominal do motor",
    unidade: "A",
    valor_min: 0,
    valor_max: 1000,
    valor_padrao: "0.0",
    grupo: "Motor",
    somente_leitura: false,
    idioma: "pt-BR",
    id_documento: null,
    pagina: 128,
    ativo: true,
    created_at: "2026-10-07T12:00:00Z",
    updated_at: "2026-10-08T12:00:00Z",
    ...parcial,
  };
}

function falha(parcial: Partial<FalhaOut> = {}): FalhaOut {
  return {
    id_falha: "ffffffff-ffff-4fff-8fff-ffffffffffff",
    id_familia: ID_FAMILIA,
    versao_firmware: "4.7 SP14",
    codigo: "F0001",
    tipo: "FALHA",
    titulo: "Sobrecorrente no motor",
    descricao: "Corrente acima do limite",
    causa: "Curto-circuito na carga",
    solucao: "Verificar o cabo do motor",
    reacao: "Desliga o motor",
    idioma: "pt-BR",
    id_documento: null,
    pagina: 212,
    ativo: true,
    created_at: "2026-10-09T12:00:00Z",
    updated_at: "2026-10-10T12:00:00Z",
    ...parcial,
  };
}

describe("Parâmetros", () => {
  it("lista aplicando família e idioma da URL", async () => {
    entrarComo("OPERADOR");
    let parametros: URLSearchParams | undefined;
    servidor.use(
      http.get("*/v1/parametros", ({ request }) => {
        parametros = new URL(request.url).searchParams;
        return HttpResponse.json({ items: [parametro()], total: 1 });
      }),
      http.get("*/v1/familias", () => HttpResponse.json({ items: [familia()], total: 1 })),
      http.get(`*/v1/familias/${ID_FAMILIA}`, () => HttpResponse.json(familia())),
    );
    renderizarApp(`/parametros?id_familia=${ID_FAMILIA}&idioma=pt-BR`);

    expect(await screen.findByText("P0305")).toBeInTheDocument();
    expect(parametros?.get("id_familia")).toBe(ID_FAMILIA);
    expect(parametros?.get("idioma")).toBe("pt-BR");
    expect(parametros?.get("limit")).toBe("20");
    expect(screen.getByText("0 – 1.000 A")).toBeInTheDocument();
    expect(within(screen.getByRole("table")).getByText("SINAMICS G120")).toBeInTheDocument();
  });
});

describe("Falhas", () => {
  it("filtra por tipo e mostra o badge do registro", async () => {
    entrarComo("OPERADOR");
    let parametros: URLSearchParams | undefined;
    servidor.use(
      http.get("*/v1/falhas", ({ request }) => {
        parametros = new URL(request.url).searchParams;
        return HttpResponse.json({ items: [falha()], total: 1 });
      }),
      http.get("*/v1/familias", () => HttpResponse.json({ items: [familia()], total: 1 })),
      http.get(`*/v1/familias/${ID_FAMILIA}`, () => HttpResponse.json(familia())),
    );
    renderizarApp(`/falhas?tipo=FALHA`);

    expect(await screen.findByText("F0001")).toBeInTheDocument();
    expect(parametros?.get("tipo")).toBe("FALHA");
    const tabela = screen.getByRole("table");
    expect(within(tabela).getByText("Sobrecorrente no motor")).toBeInTheDocument();
    expect(within(tabela).getByText("Falha", { selector: "[data-slot=badge]" })).toBeInTheDocument();
  });
});

describe("Usuários", () => {
  it("ADMIN vê a lista e o item de menu", async () => {
    entrarComo("ADMIN");
    servidor.use(http.get("*/v1/auth/usuarios", () => HttpResponse.json({ items: [usuario()], total: 1 })));
    renderizarApp("/usuarios");

    expect(await screen.findByRole("heading", { name: "Usuários" })).toBeInTheDocument();
    expect(await screen.findByText("tecnico@example.com")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Usuários" })).toBeInTheDocument();
  });

  it("perfil OPERADOR é redirecionado para o assistente", async () => {
    entrarComo("OPERADOR");
    renderizarApp("/usuarios");

    expect(await screen.findByRole("heading", { name: "Assistente" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Usuários" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Usuários" })).not.toBeInTheDocument();
  });
});
