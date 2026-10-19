import { FileText } from "lucide-react";

import type { CitacaoOut } from "@/api/gerado/modelos";
import { CodigoCopiavel } from "@/components/codigo-copiavel";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";

import type { DestinoPdf } from "./cartoes";

export function PainelCitacao({
  citacao,
  aoFechar,
  aoAbrirPdf,
}: {
  citacao: CitacaoOut | null;
  aoFechar: () => void;
  aoAbrirPdf: (destino: DestinoPdf) => void;
}) {
  return (
    <Sheet
      open={citacao !== null}
      onOpenChange={(aberto) => {
        if (!aberto) aoFechar();
      }}
    >
      <SheetContent className="flex w-full flex-col gap-0 sm:max-w-lg">
        {citacao && (
          <>
            <SheetHeader className="border-b">
              <SheetTitle>
                Fonte [{citacao.indice}] — {citacao.titulo_documento}
              </SheetTitle>
              <SheetDescription className="flex flex-wrap items-center gap-x-3 gap-y-1">
                {citacao.codigo_documento && <CodigoCopiavel codigo={citacao.codigo_documento} />}
                {citacao.secao && <span>Seção: {citacao.secao}</span>}
                {citacao.pagina !== null && <span>Página {citacao.pagina}</span>}
                <span className="tabular-nums">Relevância {citacao.score.toFixed(3)}</span>
              </SheetDescription>
            </SheetHeader>
            <ScrollArea className="min-h-0 flex-1">
              <blockquote className="m-4 border-l-4 border-primary/40 pl-4 text-sm leading-relaxed whitespace-pre-wrap">
                {citacao.trecho}
              </blockquote>
            </ScrollArea>
            <div className="border-t p-4">
              <Button
                className="w-full"
                onClick={() => {
                  aoAbrirPdf({ idDocumento: citacao.id_documento, pagina: citacao.pagina });
                }}
              >
                <FileText />
                Abrir PDF{citacao.pagina !== null ? ` na página ${citacao.pagina}` : ""}
              </Button>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
