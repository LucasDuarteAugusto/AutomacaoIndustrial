import { describe, expect, it, vi } from "vitest";

import { token } from "@/test/dados";

import {
  aoEncerrarSessao,
  destinoSeguro,
  encerrarSessao,
  iniciarSessao,
  obterSessao,
  podeEscrever,
} from "./sessao";

describe("sessão", () => {
  it("guarda token, usuário e expiração no sessionStorage", () => {
    const sessao = iniciarSessao(token("OPERADOR"));
    expect(obterSessao()).toEqual(sessao);
    expect(sessao.expiraEm).toBeGreaterThan(Date.now() + 28_000_000);
    expect(sessionStorage.getItem("automacao.sessao")).toContain("token-de-teste");
  });

  it("encerrar limpa a sessão e avisa os ouvintes com o motivo", () => {
    const ouvinte = vi.fn();
    const desligar = aoEncerrarSessao(ouvinte);
    iniciarSessao(token());

    encerrarSessao("nao-autorizado");

    expect(obterSessao()).toBeNull();
    expect(sessionStorage.getItem("automacao.sessao")).toBeNull();
    expect(ouvinte).toHaveBeenCalledWith("nao-autorizado");
    desligar();
  });

  it("sessão vencida é encerrada como expirada", () => {
    const ouvinte = vi.fn();
    const desligar = aoEncerrarSessao(ouvinte);
    iniciarSessao({ ...token(), expires_in: -1 });

    expect(obterSessao()).toBeNull();
    expect(ouvinte).toHaveBeenCalledWith("expirada");
    desligar();
  });

  it("só ADMIN e OPERADOR escrevem", () => {
    expect(podeEscrever("ADMIN")).toBe(true);
    expect(podeEscrever("OPERADOR")).toBe(true);
    expect(podeEscrever("LEITURA")).toBe(false);
  });

  it("redirect após login aceita só caminhos internos", () => {
    expect(destinoSeguro("/documentos?status_processamento=ERRO")).toBe(
      "/documentos?status_processamento=ERRO",
    );
    expect(destinoSeguro("https://malicioso.example")).toBe("/assistente");
    expect(destinoSeguro("//malicioso.example")).toBe("/assistente");
    expect(destinoSeguro(undefined)).toBe("/assistente");
  });
});
