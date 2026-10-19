import type { QueryClient } from "@tanstack/react-query";
import { createRouter, type RouterHistory } from "@tanstack/react-router";
import { toast } from "sonner";

import { configurarSessaoHttp } from "@/api/sessao-http";
import { aoEncerrarSessao, encerrarSessao, obterSessao } from "@/features/auth/sessao";
import { routeTree } from "@/routeTree.gen";

export interface ContextoRouter {
  queryClient: QueryClient;
}

function montarRouter(queryClient: QueryClient, history?: RouterHistory) {
  return createRouter({
    routeTree,
    context: { queryClient },
    defaultPreload: "intent",
    defaultPreloadStaleTime: 0,
    scrollRestoration: true,
    ...(history ? { history } : {}),
  });
}

export type Router = ReturnType<typeof montarRouter>;

/** Cria o router e liga a sessão ao cliente HTTP. `desmontar` remove o ouvinte de logout (usado nos testes). */
export function criarRouter(queryClient: QueryClient, history?: RouterHistory) {
  const router = montarRouter(queryClient, history);

  configurarSessaoHttp({
    obterToken: () => obterSessao()?.token ?? null,
    aoNaoAutorizado: () => {
      encerrarSessao("nao-autorizado");
    },
  });

  const desmontar = aoEncerrarSessao((motivo) => {
    queryClient.clear();
    if (motivo === "expirada") toast.warning("Sua sessão expirou. Entre novamente.");
    if (motivo === "nao-autorizado") toast.error("Sessão inválida. Entre novamente.");
    const { href, pathname } = router.state.location;
    const redirect = motivo === "saiu" || pathname === "/login" ? undefined : href;
    void router.navigate({ to: "/login", search: { redirect } });
  });

  return { router, desmontar };
}

declare module "@tanstack/react-router" {
  interface Register {
    router: Router;
  }
}
