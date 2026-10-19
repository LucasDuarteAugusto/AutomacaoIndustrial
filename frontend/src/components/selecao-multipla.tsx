import { X } from "lucide-react";

import { Badge } from "@/components/ui/badge";

import { ComboboxAssincrono, type ComboboxAssincronoProps, type Opcao } from "./combobox-assincrono";

type PropsBase<TDados, TErro> = Pick<
  ComboboxAssincronoProps<TDados, TErro>,
  "id" | "consulta" | "placeholder" | "desabilitado" | "aria-invalid" | "aria-describedby"
>;

interface SelecaoMultiplaProps<TDados, TErro> extends PropsBase<TDados, TErro> {
  selecionadas: Opcao[];
  aoMudar: (opcoes: Opcao[]) => void;
  mapear: (dados: TDados) => Opcao[];
}

/** Lista de escolhas em chips + combobox para adicionar (opções já escolhidas somem da lista). */
export function SelecaoMultipla<TDados, TErro = unknown>({
  selecionadas,
  aoMudar,
  mapear,
  placeholder = "Adicionar…",
  ...props
}: SelecaoMultiplaProps<TDados, TErro>) {
  const ids = new Set(selecionadas.map((o) => o.id));
  return (
    <div className="grid gap-2">
      <ComboboxAssincrono
        {...props}
        valor={undefined}
        permitirLimpar={false}
        placeholder={placeholder}
        mapear={(dados) => mapear(dados).filter((o) => !ids.has(o.id))}
        aoMudar={(opcao) => {
          if (opcao) aoMudar([...selecionadas, opcao]);
        }}
      />
      {selecionadas.length > 0 && (
        <ul className="flex flex-wrap gap-1.5">
          {selecionadas.map((opcao) => (
            <li key={opcao.id}>
              <Badge variant="secondary" className="gap-1 py-1 pr-1">
                {opcao.rotulo}
                <button
                  type="button"
                  className="rounded-sm p-0.5 hover:bg-muted-foreground/20"
                  aria-label={`Remover ${opcao.rotulo}`}
                  disabled={props.desabilitado}
                  onClick={() => {
                    aoMudar(selecionadas.filter((o) => o.id !== opcao.id));
                  }}
                >
                  <X className="size-3" />
                </button>
              </Badge>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
