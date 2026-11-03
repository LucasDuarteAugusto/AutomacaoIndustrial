import { Factory } from "lucide-react";

import { cn } from "@/lib/utils";

/** Ícone da marca — fábrica (lucide) sobre azul industrial, alinhado ao favicon. */
export function IconeMarca({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex size-6 shrink-0 items-center justify-center rounded-md bg-[#1A2B4C] text-[#10B981]",
        className,
      )}
      aria-hidden
    >
      <Factory className="size-[65%]" strokeWidth={2.5} />
    </span>
  );
}
