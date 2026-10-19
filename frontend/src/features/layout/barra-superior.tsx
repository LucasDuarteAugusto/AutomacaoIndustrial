import { LogOut, Menu, Moon, Sun, UserRound } from "lucide-react";
import { useState } from "react";

import { useReady } from "@/api/gerado/health/health";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { DialogoMinhaConta } from "@/features/auth/dialogo-minha-conta";
import { encerrarSessao, type Sessao } from "@/features/auth/sessao";
import { ROTULO_PERFIL } from "@/lib/rotulos";
import { useTema } from "@/lib/tema";
import { cn } from "@/lib/utils";

import { Marca, Navegacao } from "./navegacao";

function MenuMobile() {
  const [aberto, setAberto] = useState(false);
  return (
    <Sheet open={aberto} onOpenChange={setAberto}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="md:hidden" aria-label="Abrir menu">
          <Menu />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-64 bg-sidebar p-0">
        <SheetHeader className="sr-only">
          <SheetTitle>Menu</SheetTitle>
        </SheetHeader>
        <Marca />
        <Navegacao
          aoNavegar={() => {
            setAberto(false);
          }}
        />
      </SheetContent>
    </Sheet>
  );
}

function IndicadorStatus() {
  const ready = useReady({ query: { refetchInterval: 30_000, retry: false, staleTime: 0 } });
  const ok = ready.isSuccess;
  const texto = ready.isPending
    ? "Verificando servidor…"
    : ok
      ? "Servidor e banco disponíveis"
      : "Servidor indisponível";
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span role="status" aria-label={texto} className="flex size-9 items-center justify-center">
          <span
            className={cn(
              "size-2.5 rounded-full",
              ready.isPending ? "bg-muted-foreground" : ok ? "bg-sucesso" : "animate-pulse bg-destructive",
            )}
          />
        </span>
      </TooltipTrigger>
      <TooltipContent>{texto}</TooltipContent>
    </Tooltip>
  );
}

function AlternarTema() {
  const [tema, alternar] = useTema();
  const rotulo = tema === "escuro" ? "Usar tema claro" : "Usar tema escuro";
  return (
    <Button variant="ghost" size="icon" onClick={alternar} aria-label={rotulo} title={rotulo}>
      {tema === "escuro" ? <Sun /> : <Moon />}
    </Button>
  );
}

function MenuUsuario({ sessao }: { sessao: Sessao }) {
  const [contaAberta, setContaAberta] = useState(false);
  const { usuario } = sessao;
  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="gap-2 px-2" aria-label="Menu do usuário">
            <span className="flex size-7 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
              {usuario.nome.slice(0, 1).toUpperCase()}
            </span>
            <span className="hidden max-w-40 truncate text-sm sm:inline">{usuario.nome}</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-60">
          <DropdownMenuLabel className="grid gap-1">
            <span className="truncate">{usuario.nome}</span>
            <span className="truncate text-xs font-normal text-muted-foreground">{usuario.email}</span>
            <Badge variant="secondary" className="w-fit">
              {ROTULO_PERFIL[usuario.perfil]}
            </Badge>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onSelect={() => {
              setContaAberta(true);
            }}
          >
            <UserRound /> Minha conta
          </DropdownMenuItem>
          <DropdownMenuItem
            onSelect={() => {
              encerrarSessao("saiu");
            }}
          >
            <LogOut /> Sair
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <DialogoMinhaConta aberto={contaAberta} aoMudar={setContaAberta} />
    </>
  );
}

export function BarraSuperior({ sessao }: { sessao: Sessao }) {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-1 border-b bg-background/95 px-2 backdrop-blur md:px-4">
      <MenuMobile />
      <div className="flex-1" />
      <IndicadorStatus />
      <AlternarTema />
      <MenuUsuario sessao={sessao} />
    </header>
  );
}
