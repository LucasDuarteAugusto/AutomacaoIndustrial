import { CircleAlert, CircleCheck, Clock, Loader2 } from "lucide-react";

import type { StatusProcessamento } from "@/api/gerado/modelos";
import { Badge } from "@/components/ui/badge";
import { ROTULO_STATUS } from "@/lib/rotulos";
import { cn } from "@/lib/utils";

const ESTILO: Record<StatusProcessamento, { classe: string; icone: typeof Clock }> = {
  PENDENTE: { classe: "bg-muted text-muted-foreground", icone: Clock },
  PROCESSANDO: { classe: "bg-info/15 text-info", icone: Loader2 },
  INDEXADO: { classe: "bg-sucesso/15 text-sucesso", icone: CircleCheck },
  ERRO: { classe: "bg-destructive/15 text-destructive", icone: CircleAlert },
};

export function StatusBadge({ status }: { status: StatusProcessamento }) {
  const { classe, icone: Icone } = ESTILO[status];
  return (
    <Badge variant="outline" className={cn("gap-1 border-transparent", classe)}>
      <Icone className={cn("size-3", status === "PROCESSANDO" && "animate-spin")} aria-hidden />
      {ROTULO_STATUS[status]}
    </Badge>
  );
}
