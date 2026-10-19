import { cloneElement, type ReactElement } from "react";

import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

interface CampoProps {
  id: string;
  rotulo: string;
  erro?: string | undefined;
  dica?: string;
  className?: string;
  children: ReactElement<{ id?: string; "aria-invalid"?: boolean; "aria-describedby"?: string }>;
}

/** Rótulo + controle + mensagem de erro, com ids e aria ligados. */
export function Campo({ id, rotulo, erro, dica, className, children }: CampoProps) {
  const descricoes = [dica && `${id}-dica`, erro && `${id}-erro`].filter(Boolean).join(" ") || undefined;
  return (
    <div className={cn("grid gap-1.5", className)}>
      <Label htmlFor={id}>{rotulo}</Label>
      {cloneElement(children, {
        id,
        "aria-invalid": erro ? true : undefined,
        "aria-describedby": descricoes,
      })}
      {dica && !erro && (
        <p id={`${id}-dica`} className="text-xs text-muted-foreground">
          {dica}
        </p>
      )}
      {erro && (
        <p id={`${id}-erro`} role="alert" className="text-xs text-destructive">
          {erro}
        </p>
      )}
    </div>
  );
}
