import { Check, Copy } from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";

/** Código técnico (p1120, F07801, MLFB) em fonte monoespaçada, com botão de copiar. */
export function CodigoCopiavel({ codigo, className }: { codigo: string; className?: string }) {
  const [copiado, setCopiado] = useState(false);
  return (
    <span className={cn("inline-flex items-center gap-1", className)}>
      <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.9em]">{codigo}</code>
      <button
        type="button"
        className="rounded p-1 text-muted-foreground hover:text-foreground"
        aria-label={`Copiar ${codigo}`}
        title="Copiar"
        onClick={() => {
          void navigator.clipboard.writeText(codigo).then(() => {
            setCopiado(true);
            window.setTimeout(() => {
              setCopiado(false);
            }, 1500);
          });
        }}
      >
        {copiado ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
      </button>
    </span>
  );
}
