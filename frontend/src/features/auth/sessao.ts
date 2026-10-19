import { useSyncExternalStore } from "react";

import type { Perfil, TokenOut, UsuarioOut } from "@/api/gerado/modelos";

export interface Sessao {
  token: string;
  /** Epoch em ms. */
  expiraEm: number;
  usuario: UsuarioOut;
}

export type MotivoEncerramento = "saiu" | "expirada" | "nao-autorizado";

const CHAVE = "automacao.sessao";
const ouvintes = new Set<() => void>();
const ouvintesEncerramento = new Set<(motivo: MotivoEncerramento) => void>();

function carregar(): Sessao | null {
  try {
    const bruto = sessionStorage.getItem(CHAVE);
    if (!bruto) return null;
    const sessao = JSON.parse(bruto) as Sessao;
    return sessao.expiraEm > Date.now() ? sessao : null;
  } catch {
    return null;
  }
}

let atual: Sessao | null = carregar();

function definir(sessao: Sessao | null) {
  atual = sessao;
  if (sessao) sessionStorage.setItem(CHAVE, JSON.stringify(sessao));
  else sessionStorage.removeItem(CHAVE);
  for (const ouvinte of ouvintes) ouvinte();
}

export function obterSessao(): Sessao | null {
  if (atual && atual.expiraEm <= Date.now()) encerrarSessao("expirada");
  return atual;
}

export function iniciarSessao(token: TokenOut): Sessao {
  const sessao: Sessao = {
    token: token.access_token,
    expiraEm: Date.now() + token.expires_in * 1000,
    usuario: token.usuario,
  };
  definir(sessao);
  return sessao;
}

export function atualizarUsuario(usuario: UsuarioOut) {
  if (atual) definir({ ...atual, usuario });
}

export function encerrarSessao(motivo: MotivoEncerramento) {
  if (!atual) return;
  definir(null);
  for (const ouvinte of ouvintesEncerramento) ouvinte(motivo);
}

export function aoEncerrarSessao(ouvinte: (motivo: MotivoEncerramento) => void): () => void {
  ouvintesEncerramento.add(ouvinte);
  return () => ouvintesEncerramento.delete(ouvinte);
}

function assinar(ouvinte: () => void) {
  ouvintes.add(ouvinte);
  return () => ouvintes.delete(ouvinte);
}

export function useSessao(): Sessao | null {
  return useSyncExternalStore(assinar, () => atual);
}

export function podeEscrever(perfil: Perfil | undefined): boolean {
  return perfil === "ADMIN" || perfil === "OPERADOR";
}

export function usePodeEscrever(): boolean {
  return podeEscrever(useSessao()?.usuario.perfil);
}

/** Aceita só caminhos internos (evita open redirect via ?redirect=). */
export function destinoSeguro(redirect: string | undefined): string {
  return redirect?.startsWith("/") && !redirect.startsWith("//") ? redirect : "/assistente";
}
