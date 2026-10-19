import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { obterSessao } from "@/features/auth/sessao";

/** Respostas padrão para o app subir; cada teste sobrescreve com `servidor.use(...)`. */
export const servidor = setupServer(
  http.get("*/ready", () => HttpResponse.json({ status: "ok" })),
  http.get("*/v1/auth/bootstrap", () => HttpResponse.json({ necessario: false })),
  http.get("*/v1/auth/me", () => {
    const sessao = obterSessao();
    return sessao
      ? HttpResponse.json(sessao.usuario)
      : HttpResponse.json({ title: "Não autorizado", status: 401 }, { status: 401 });
  }),
);

export function problema(
  status: number,
  titulo: string,
  detalhe?: string,
  extras: Record<string, unknown> = {},
) {
  return HttpResponse.json(
    { type: "about:blank", title: titulo, status, detail: detalhe ?? null, instance: "/teste", ...extras },
    { status, headers: { "Content-Type": "application/problem+json" } },
  );
}
