import { createFileRoute, Navigate, Outlet, redirect, useLocation } from "@tanstack/react-router";

import { getMeQueryOptions } from "@/api/gerado/auth/auth";
import { ehProblema } from "@/api/problema";
import { atualizarUsuario, obterSessao, useSessao } from "@/features/auth/sessao";
import { useAvisoExpiracao } from "@/features/auth/use-aviso-expiracao";
import { BarraSuperior } from "@/features/layout/barra-superior";
import { Marca, Navegacao } from "@/features/layout/navegacao";

export const Route = createFileRoute("/_app")({
  beforeLoad: async ({ context, location }) => {
    if (!obterSessao()) throw redirect({ to: "/login", search: { redirect: location.href } });
    try {
      const usuario = await context.queryClient.query({
        ...getMeQueryOptions(),
        staleTime: 5 * 60_000,
      });
      atualizarUsuario(usuario);
    } catch (erro) {
      if (ehProblema(erro, 401)) throw redirect({ to: "/login", search: { redirect: location.href } });
      // Rede/servidor fora: segue com o usuário salvo na sessão; as telas mostram o erro.
    }
  },
  component: LayoutApp,
});

function LayoutApp() {
  const sessao = useSessao();
  const location = useLocation();
  useAvisoExpiracao(sessao?.expiraEm);

  if (!sessao) return <Navigate to="/login" search={{ redirect: location.href }} />;

  return (
    <div className="flex min-h-svh">
      <aside className="sticky top-0 hidden h-svh w-60 shrink-0 flex-col border-r bg-sidebar md:flex">
        <Marca />
        <Navegacao />
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <BarraSuperior sessao={sessao} />
        <main className="flex-1 p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
