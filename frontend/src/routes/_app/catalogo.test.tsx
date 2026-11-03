import { screen, waitFor, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import type { EquipamentoOut, FabricanteOut, FamiliaOut, TipoEquipamentoOut } from "@/api/gerado/modelos";
import { entrarComo } from "@/test/dados";
import { problema, servidor } from "@/test/servidor";
import { renderizarApp } from "@/test/utils";

const ID_FABRICANTE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const ID_TIPO = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb";
const ID_FAMILIA = "cccccccc-cccc-4ccc-8ccc-cccccccccccc";
const ID_EQUIPAMENTO = "dddddddd-dddd-4ddd-8ddd-dddddddddddd";

function fabricante(parcial: Partial<FabricanteOut> = {}): FabricanteOut {
  return {
    id_fabricante: ID_FABRICANTE,
    nome: "Siemens",
    site: "https://www.siemens.com",
    ativo: true,
    created_at: "2026-10-01T12:00:00Z",
    updated_at: "2026-10-02T12:00:00Z",
    ...parcial,
  };
}

function tipo(parcial: Partial<TipoEquipamentoOut> = {}): TipoEquipamentoOut {
  return {
    id_tipo_equipamento: ID_TIPO,
    codigo: "INVERSOR",
    nome: "Inversor de frequência",
    descricao: null,
    ...parcial,
  };
}

function familia(parcial: Partial<FamiliaOut> = {}): FamiliaOut {
  return {
    id_familia: ID_FAMILIA,
    id_fabricante: ID_FABRICANTE,
    id_tipo_equipamento: ID_TIPO,
    nome: "SINAMICS G120",
    descricao: "Inversores de 0,37 a 250 kW",
    ativo: true,
    created_at: "2026-10-03T12:00:00Z",
    updated_at: "2026-10-04T12:00:00Z",
    ...parcial,
  };
}

function equipamento(parcial: Partial<EquipamentoOut> = {}): EquipamentoOut {
  return {
    id_equipamento: ID_EQUIPAMENTO,
    id_familia: ID_FAMILIA,
    codigo_pedido: "6SL3210-1KE21-3UF1",
    nome: "SINAMICS G120C 3 kW",
    potencia_kw: 3,
    tensao_nominal_v: 380,
    corrente_nominal_a: 7.3,
    ativo: true,
    created_at: "2026-10-05T12:00:00Z",
    updated_at: "2026-10-06T12:00:00Z",
    ...parcial,
  };
}

describe("Catálogo — fabricantes", () => {
  it("lista aplicando busca e situação da URL", async () => {
    entrarComo("OPERADOR");
    let parametros: URLSearchParams | undefined;
    servidor.use(
      http.get("*/v1/fabricantes", ({ request }) => {
        parametros = new URL(request.url).searchParams;
        return HttpResponse.json({ items: [fabricante()], total: 1 });
      }),
    );
    renderizarApp("/fabricantes?busca=Sie&ativo=true");

    expect(await screen.findByText("Siemens")).toBeInTheDocument();
    expect(parametros?.get("busca")).toBe("Sie");
    expect(parametros?.get("ativo")).toBe("true");
    expect(parametros?.get("limit")).toBe("20");
    expect(screen.getByRole("button", { name: /Novo fabricante/ })).toBeInTheDocument();
  });

  it("perfil LEITURA não vê ações de escrita", async () => {
    entrarComo("LEITURA");
    servidor.use(http.get("*/v1/fabricantes", () => HttpResponse.json({ items: [fabricante()], total: 1 })));
    renderizarApp("/fabricantes");

    expect(await screen.findByText("Siemens")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Novo fabricante/ })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Editar Siemens")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Excluir Siemens")).not.toBeInTheDocument();
  });

  it("exclusão com 409 oferece desativar o registro", async () => {
    entrarComo("ADMIN");
    let corpoDoPatch: unknown;
    servidor.use(
      http.get("*/v1/fabricantes", () => HttpResponse.json({ items: [fabricante()], total: 1 })),
      http.delete(`*/v1/fabricantes/${ID_FABRICANTE}`, () =>
        problema(409, "Conflito", "Fabricante possui famílias vinculadas"),
      ),
      http.patch(`*/v1/fabricantes/${ID_FABRICANTE}`, async ({ request }) => {
        corpoDoPatch = await request.json();
        return HttpResponse.json(fabricante({ ativo: false }));
      }),
    );
    const { usuario } = renderizarApp("/fabricantes");

    await usuario.click(await screen.findByLabelText("Excluir Siemens"));
    const dialogo = await screen.findByRole("dialog");
    await usuario.click(within(dialogo).getByRole("button", { name: "Excluir" }));

    expect(await screen.findByText("Fabricante com vínculos não pode ser excluído.")).toBeInTheDocument();
    await usuario.click(screen.getByRole("button", { name: "Desativar" }));

    await waitFor(() => {
      expect(corpoDoPatch).toEqual({ ativo: false });
    });
  });
});

describe("Catálogo — famílias", () => {
  it("filtra por fabricante e resolve os nomes das colunas", async () => {
    entrarComo("OPERADOR");
    let parametros: URLSearchParams | undefined;
    servidor.use(
      http.get("*/v1/familias", ({ request }) => {
        parametros = new URL(request.url).searchParams;
        return HttpResponse.json({ items: [familia()], total: 1 });
      }),
      http.get("*/v1/fabricantes", () => HttpResponse.json({ items: [fabricante()], total: 1 })),
      http.get(`*/v1/fabricantes/${ID_FABRICANTE}`, () => HttpResponse.json(fabricante())),
      http.get("*/v1/tipos-equipamento", () => HttpResponse.json({ items: [tipo()], total: 1 })),
    );
    renderizarApp(`/familias?id_fabricante=${ID_FABRICANTE}`);

    expect(await screen.findByText("SINAMICS G120")).toBeInTheDocument();
    expect(parametros?.get("id_fabricante")).toBe(ID_FABRICANTE);
    const tabela = screen.getByRole("table");
    expect(within(tabela).getByText("Siemens")).toBeInTheDocument();
    expect(within(tabela).getByText("Inversor de frequência")).toBeInTheDocument();
  });
});

describe("Catálogo — equipamentos", () => {
  it("filtra por família e mostra os dados nominais formatados", async () => {
    entrarComo("OPERADOR");
    let parametros: URLSearchParams | undefined;
    servidor.use(
      http.get("*/v1/equipamentos", ({ request }) => {
        parametros = new URL(request.url).searchParams;
        return HttpResponse.json({ items: [equipamento()], total: 1 });
      }),
      http.get("*/v1/familias", () => HttpResponse.json({ items: [familia()], total: 1 })),
      http.get(`*/v1/familias/${ID_FAMILIA}`, () => HttpResponse.json(familia())),
    );
    renderizarApp(`/equipamentos?id_familia=${ID_FAMILIA}`);

    expect(await screen.findByText("6SL3210-1KE21-3UF1")).toBeInTheDocument();
    expect(parametros?.get("id_familia")).toBe(ID_FAMILIA);
    expect(screen.getByText("380 V / 7,3 A")).toBeInTheDocument();
    expect(within(screen.getByRole("table")).getByText("SINAMICS G120")).toBeInTheDocument();
  });
});
