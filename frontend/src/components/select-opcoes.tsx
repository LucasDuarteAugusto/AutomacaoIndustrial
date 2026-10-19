import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";

const TODOS = "__todos__";

interface SelectOpcoesProps<V extends string> {
  id?: string;
  valor: V | undefined;
  aoMudar: (valor: V | undefined) => void;
  opcoes: readonly V[];
  rotulos: Record<V, string>;
  /** Sem `rotuloTodos`, a escolha é obrigatória. */
  rotuloTodos?: string;
  placeholder?: string;
  className?: string;
  "aria-invalid"?: boolean;
  "aria-describedby"?: string;
}

/** Select de enum da API; "Todos" vira `undefined` (o Radix não aceita valor vazio). */
export function SelectOpcoes<V extends string>({
  id,
  valor,
  aoMudar,
  opcoes,
  rotulos,
  rotuloTodos,
  placeholder = "Selecione…",
  className,
  ...aria
}: SelectOpcoesProps<V>) {
  return (
    <Select
      value={valor ?? (rotuloTodos ? TODOS : "")}
      onValueChange={(novo) => {
        aoMudar(novo === TODOS ? undefined : (novo as V));
      }}
    >
      <SelectTrigger id={id} className={cn("w-full", className)} {...aria}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {rotuloTodos && <SelectItem value={TODOS}>{rotuloTodos}</SelectItem>}
        {opcoes.map((opcao) => (
          <SelectItem key={opcao} value={opcao}>
            {rotulos[opcao]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
