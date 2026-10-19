import type { QueryClient } from "@tanstack/react-query";
import { createRouter } from "@tanstack/react-router";
import { toast } from "sonner";

import { configurarSessaoHttp } from "@/api/sessao-http";
import { aoEncerrarSessao, encerrarSessao, obterSessao } from "@/features/auth/sessao";
import { routeTree } from "@/routeTree.gen";

export interface ContextoRouter {
  queryClient: QueryClient;
}

export function criarRouter(queryClient: QueryClient) {
  const router = createRouter({
    routeTree,
    context: { queryClient },
    defaultPreload: "intent",
    defaultPreloadStaleTime: 0,
    scrollRestoration: true,
  });

  configurarSessaoHttp({
    obterToken: () => obterSessao()?.token ?? null,
    aoNaoAutorizado: () => {
      encerrarSessao("nao-autorizado");
    },
  });

  aoEncerrarSessao((motivo) => {
    queryClient.clear();
    if (motivo === "expirada") toast.warning("Sua sessão expirou. Entre novamente.");
    if (motivo === "nao-autorizado") toast.error("Sessão inválida. Entre novamente.");
    const { href, pathname } = router.state.location;
    const redirect = motivo === "saiu" || pathname === "/login" ? undefined : href;
    void router.navigate({ to: "/login", search: { redirect } });
  });

  return router;
}

declare module "@tanstack/react-router" {
  interface Register {
    router: ReturnType<typeof criarRouter>;
  }
}
