import { Link } from "@tanstack/react-router";
import { FileText, MessageSquareText, Search } from "lucide-react";

const ITENS = [
  { to: "/assistente", rotulo: "Assistente", icone: MessageSquareText },
  { to: "/busca", rotulo: "Busca", icone: Search },
  { to: "/documentos", rotulo: "Documentos", icone: FileText },
] as const;

export function Navegacao({ aoNavegar }: { aoNavegar?: () => void }) {
  return (
    <nav aria-label="Principal" className="grid gap-1 p-2">
      {ITENS.map(({ to, rotulo, icone: Icone }) => (
        <Link
          key={to}
          to={to}
          onClick={aoNavegar}
          className="flex min-h-11 items-center gap-3 rounded-md px-3 text-sm font-medium text-sidebar-foreground/80 transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          activeProps={{ className: "bg-sidebar-accent text-sidebar-accent-foreground" }}
        >
          <Icone className="size-4" aria-hidden />
          {rotulo}
        </Link>
      ))}
    </nav>
  );
}

export function Marca() {
  return (
    <Link to="/assistente" className="flex h-14 items-center gap-2 border-b px-4 font-semibold">
      <img src="/favicon.svg" alt="" className="size-6" />
      Automação Industrial
    </Link>
  );
}
