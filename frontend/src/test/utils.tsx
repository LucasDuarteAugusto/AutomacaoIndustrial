import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryHistory, RouterProvider } from "@tanstack/react-router";
import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Toaster } from "sonner";

import { criarRouter } from "@/app/router";
import { TooltipProvider } from "@/components/ui/tooltip";

const desmontagens: (() => void)[] = [];

export function desmontarApps() {
  while (desmontagens.length) desmontagens.pop()?.();
}

/** Renderiza o app completo (rotas, guarda, providers) a partir de `caminho`. */
export function renderizarApp(caminho: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 0 }, mutations: { retry: false } },
  });
  const { router, desmontar } = criarRouter(queryClient, createMemoryHistory({ initialEntries: [caminho] }));
  desmontagens.push(desmontar);
  const resultado = render(
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <RouterProvider router={router} />
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>,
  );
  return { ...resultado, router, queryClient, usuario: userEvent.setup() };
}
