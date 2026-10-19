import { useQuery, type UseQueryOptions } from "@tanstack/react-query";
import { Check, ChevronsUpDown, Loader2, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useDebounce } from "@/lib/use-debounce";
import { cn } from "@/lib/utils";

export interface Opcao {
  id: string;
  rotulo: string;
  detalhe?: string | undefined;
  /** Dado extra que o chamador quer guardar junto (ex.: família do equipamento). */
  meta?: string | undefined;
}

export interface ComboboxAssincronoProps<TDados, TErro = unknown> {
  id?: string;
  valor: string | undefined;
  aoMudar: (opcao: Opcao | undefined) => void;
  /** Opções da API filtradas pelo texto digitado (busca no servidor, com debounce). */
  consulta: (busca: string) => UseQueryOptions<TDados, TErro>;
  mapear: (dados: TDados) => Opcao[];
  /** Rótulo do valor atual quando ele não está na página de opções (ex.: veio da URL). */
  rotuloSelecionado?: string | undefined;
  placeholder?: string;
  desabilitado?: boolean;
  permitirLimpar?: boolean;
  className?: string;
  "aria-invalid"?: boolean;
  "aria-describedby"?: string;
}

export function ComboboxAssincrono<TDados, TErro = unknown>({
  id,
  valor,
  aoMudar,
  consulta,
  mapear,
  rotuloSelecionado,
  placeholder = "Selecione…",
  desabilitado = false,
  permitirLimpar = true,
  className,
  ...aria
}: ComboboxAssincronoProps<TDados, TErro>) {
  const [aberto, setAberto] = useState(false);
  const [busca, setBusca] = useState("");
  const buscaAtrasada = useDebounce(busca.trim());
  const resultado = useQuery({ ...consulta(buscaAtrasada), enabled: aberto && !desabilitado });
  const opcoes = resultado.data ? mapear(resultado.data) : [];
  const rotulo = opcoes.find((o) => o.id === valor)?.rotulo ?? rotuloSelecionado;

  return (
    <div className={cn("flex gap-1", className)}>
      <Popover
        open={aberto}
        onOpenChange={(novo) => {
          setAberto(novo);
          if (!novo) setBusca("");
        }}
      >
        <PopoverTrigger asChild>
          <Button
            id={id}
            type="button"
            variant="outline"
            role="combobox"
            aria-expanded={aberto}
            disabled={desabilitado}
            className="min-w-0 flex-1 justify-between font-normal"
            {...aria}
          >
            <span className={cn("truncate", !valor && "text-muted-foreground")}>
              {valor ? (rotulo ?? "Carregando…") : placeholder}
            </span>
            <ChevronsUpDown className="opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-(--radix-popover-trigger-width) min-w-64 p-0" align="start">
          <Command shouldFilter={false}>
            <CommandInput placeholder="Digite para buscar…" value={busca} onValueChange={setBusca} />
            <CommandList>
              {resultado.isFetching && (
                <div className="flex items-center gap-2 p-3 text-sm text-muted-foreground">
                  <Loader2 className="size-4 animate-spin" /> Buscando…
                </div>
              )}
              {!resultado.isFetching && <CommandEmpty>Nada encontrado.</CommandEmpty>}
              <CommandGroup>
                {opcoes.map((opcao) => (
                  <CommandItem
                    key={opcao.id}
                    value={opcao.id}
                    onSelect={() => {
                      aoMudar(opcao);
                      setAberto(false);
                      setBusca("");
                    }}
                  >
                    <Check className={cn("size-4", opcao.id === valor ? "opacity-100" : "opacity-0")} />
                    <span className="min-w-0 flex-1 truncate">{opcao.rotulo}</span>
                    {opcao.detalhe && (
                      <span className="truncate text-xs text-muted-foreground">{opcao.detalhe}</span>
                    )}
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
      {permitirLimpar && valor && !desabilitado && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label="Limpar seleção"
          onClick={() => {
            aoMudar(undefined);
          }}
        >
          <X />
        </Button>
      )}
    </div>
  );
}
