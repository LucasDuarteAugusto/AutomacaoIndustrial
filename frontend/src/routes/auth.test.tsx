import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { obterSessao } from "@/features/auth/sessao";
import { token } from "@/test/dados";
import { problema, servidor } from "@/test/servidor";
import { renderizarApp } from "@/test/utils";

describe("autenticação", () => {
  it("rota protegida sem sessão vai para o login guardando o destino", async () => {
    const { router } = renderizarApp("/documentos?status_processamento=ERRO");

    expect(await screen.findByRole("heading", { name: "Entrar" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/login");
    expect(router.state.location.search).toEqual({ redirect: "/documentos?status_processamento=ERRO" });
  });

  it("base sem usuários leva ao primeiro acesso", async () => {
    servidor.use(http.get("*/v1/auth/bootstrap", () => HttpResponse.json({ necessario: true })));
    const { router } = renderizarApp("/login");

    expect(await screen.findByRole("heading", { name: "Primeiro acesso" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/primeiro-acesso");
  });

  it("login válido abre a sessão e volta ao destino", async () => {
    servidor.use(
      http.post("*/v1/auth/login", () => HttpResponse.json(token("OPERADOR"))),
      http.get("*/v1/documentos", () => HttpResponse.json({ items: [], total: 0 })),
    );
    const { usuario, router } = renderizarApp("/login?redirect=%2Fdocumentos");

    await usuario.type(await screen.findByLabelText("E-mail"), "tecnico@example.com");
    await usuario.type(screen.getByLabelText("Senha"), "senha-forte");
    await usuario.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("heading", { name: "Documentos" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/documentos");
    expect(obterSessao()?.usuario.perfil).toBe("OPERADOR");
  });

  it("senha errada mostra mensagem sem sair da tela", async () => {
    servidor.use(
      http.post("*/v1/auth/login", () => problema(401, "Não autorizado", "E-mail ou senha inválidos.")),
    );
    const { usuario } = renderizarApp("/login");

    await usuario.type(await screen.findByLabelText("E-mail"), "tecnico@example.com");
    await usuario.type(screen.getByLabelText("Senha"), "errada1");
    await usuario.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByText("E-mail ou senha inválidos.")).toBeInTheDocument();
    expect(obterSessao()).toBeNull();
  });

  it("valida o formulário no navegador antes de chamar a API", async () => {
    const { usuario } = renderizarApp("/login");

    await usuario.type(await screen.findByLabelText("E-mail"), "invalido");
    await usuario.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => {
      expect(screen.getByLabelText("E-mail")).toHaveAttribute("aria-invalid", "true");
    });
  });
});
