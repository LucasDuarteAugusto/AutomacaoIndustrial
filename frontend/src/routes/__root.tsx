import { createRootRouteWithContext, Link, Outlet } from "@tanstack/react-router";

import type { ContextoRouter } from "@/app/router";
import { Button } from "@/components/ui/button";

export const Route = createRootRouteWithContext<ContextoRouter>()({
  component: Outlet,
  notFoundComponent: () => (
    <main className="grid min-h-svh place-items-center p-6 text-center">
      <div className="space-y-3">
        <p className="text-sm text-muted-foreground">Erro 404</p>
        <h1 className="text-2xl font-semibold">Página não encontrada</h1>
        <Button asChild>
          <Link to="/">Voltar ao início</Link>
        </Button>
      </div>
    </main>
  ),
});
