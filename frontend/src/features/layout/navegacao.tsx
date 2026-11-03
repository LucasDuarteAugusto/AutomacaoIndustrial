import { Link } from "@tanstack/react-router";
import {
  Cpu,
  Factory,
  FileText,
  Layers,
  MessageSquareText,
  Search,
  SlidersHorizontal,
  TriangleAlert,
  Users,
} from "lucide-react";

import { useEhAdmin } from "@/features/auth/sessao";

import { IconeMarca } from "./icone-marca";

const ITENS = [
  { to: "/assistente", rotulo: "Assistente", icone: MessageSquareText },
  { to: "/busca", rotulo: "Busca", icone: Search },
  { to: "/documentos", rotulo: "Documentos", icone: FileText },
  { to: "/fabricantes", rotulo: "Fabricantes", icone: Factory },
  { to: "/familias", rotulo: "Famílias", icone: Layers },
  { to: "/equipamentos", rotulo: "Equipamentos", icone: Cpu },
  { to: "/parametros", rotulo: "Parâmetros", icone: SlidersHorizontal },
  { to: "/falhas", rotulo: "Falhas", icone: TriangleAlert },
] as const;

const ITENS_ADMIN = [{ to: "/usuarios", rotulo: "Usuários", icone: Users }] as const;

export function Navegacao({ aoNavegar }: { aoNavegar?: () => void }) {
  const ehAdmin = useEhAdmin();
  const itens = ehAdmin ? [...ITENS, ...ITENS_ADMIN] : ITENS;
  return (
    <nav aria-label="Principal" className="grid gap-1 p-2">
      {itens.map(({ to, rotulo, icone: Icone }) => (
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
    <Link
      to="/assistente"
      className="flex h-14 items-center gap-2 border-b border-sidebar-border px-4 font-semibold text-sidebar-foreground"
    >
      <IconeMarca />
      DrivePilot
    </Link>
  );
}
