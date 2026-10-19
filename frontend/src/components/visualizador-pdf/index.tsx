import { Loader2 } from "lucide-react";
import { lazy, Suspense } from "react";

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";

import type { ConteudoVisualizadorProps } from "./conteudo";

const Conteudo = lazy(() => import("./conteudo"));

export interface PdfAberto extends ConteudoVisualizadorProps {
  rotuloPagina?: string | undefined;
}

/** Diálogo com o PDF do documento, aberto na página indicada. O pdf.js só é baixado na primeira abertura. */
export function VisualizadorPdf({ pdf, aoFechar }: { pdf: PdfAberto | null; aoFechar: () => void }) {
  return (
    <Dialog
      open={pdf !== null}
      onOpenChange={(aberto) => {
        if (!aberto) aoFechar();
      }}
    >
      <DialogContent className="flex h-[90svh] max-w-[min(96vw,1100px)] flex-col gap-0 p-0 sm:max-w-[min(96vw,1100px)]">
        <DialogHeader className="border-b px-4 py-3 pr-12">
          <DialogTitle className="truncate">{pdf?.titulo}</DialogTitle>
          <DialogDescription>{pdf?.rotuloPagina ?? "Documento técnico"}</DialogDescription>
        </DialogHeader>
        {pdf && (
          <Suspense
            fallback={
              <div className="flex flex-1 items-center justify-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" /> Carregando visualizador…
              </div>
            }
          >
            <Conteudo key={`${pdf.idDocumento}-${pdf.paginaInicial ?? 1}`} {...pdf} />
          </Suspense>
        )}
      </DialogContent>
    </Dialog>
  );
}
