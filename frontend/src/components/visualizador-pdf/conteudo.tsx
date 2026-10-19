import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Download, ExternalLink, Loader2, ZoomIn, ZoomOut } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";

import { getBaixarArquivoDocumentoQueryOptions } from "@/api/gerado/documentos/documentos";
import { ProblemaAlerta } from "@/components/problema-alerta";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

// eval desligado: compatível com a CSP do nginx.
const OPCOES_PDF = { isEvalSupported: false };
const ESCALAS = [0.75, 1, 1.25, 1.5, 2];

export interface ConteudoVisualizadorProps {
  idDocumento: string;
  titulo: string;
  paginaInicial?: number | null | undefined;
}

function useLarguraElemento<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [largura, setLargura] = useState(0);
  useEffect(() => {
    const elemento = ref.current;
    if (!elemento) return;
    const observador = new ResizeObserver(([entrada]) => {
      if (entrada) setLargura(entrada.contentRect.width);
    });
    observador.observe(elemento);
    return () => {
      observador.disconnect();
    };
  }, []);
  return [ref, largura] as const;
}

export default function ConteudoVisualizador({
  idDocumento,
  titulo,
  paginaInicial,
}: ConteudoVisualizadorProps) {
  const arquivo = useQuery({ ...getBaixarArquivoDocumentoQueryOptions(idDocumento), staleTime: Infinity });
  const [pagina, setPagina] = useState(paginaInicial ?? 1);
  const [total, setTotal] = useState<number>();
  const [indiceEscala, setIndiceEscala] = useState(1);
  const [refArea, largura] = useLarguraElemento<HTMLDivElement>();

  const urlObjeto = useMemo(
    () => (arquivo.data ? URL.createObjectURL(arquivo.data) : undefined),
    [arquivo.data],
  );
  useEffect(
    () => () => {
      if (urlObjeto) URL.revokeObjectURL(urlObjeto);
    },
    [urlObjeto],
  );

  const escala = ESCALAS[indiceEscala] ?? 1;
  const larguraPagina = Math.max(240, Math.min(largura - 32, 900)) * escala;
  const irPara = (destino: number) => {
    setPagina(Math.min(Math.max(1, destino), total ?? destino));
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex flex-wrap items-center gap-2 border-b px-4 py-2">
        <Button
          variant="outline"
          size="icon"
          aria-label="Página anterior"
          disabled={pagina <= 1}
          onClick={() => irPara(pagina - 1)}
        >
          <ChevronLeft />
        </Button>
        <label className="flex items-center gap-2 text-sm">
          Página
          <Input
            type="number"
            min={1}
            max={total}
            value={pagina}
            onChange={(e) => irPara(Number(e.target.value) || 1)}
            className="h-8 w-20"
          />
          <span className="text-muted-foreground">de {total ?? "…"}</span>
        </label>
        <Button
          variant="outline"
          size="icon"
          aria-label="Próxima página"
          disabled={total === undefined || pagina >= total}
          onClick={() => irPara(pagina + 1)}
        >
          <ChevronRight />
        </Button>
        <div className="mx-2 h-6 w-px bg-border" />
        <Button
          variant="outline"
          size="icon"
          aria-label="Diminuir zoom"
          disabled={indiceEscala === 0}
          onClick={() => setIndiceEscala((i) => i - 1)}
        >
          <ZoomOut />
        </Button>
        <span className="w-12 text-center text-sm tabular-nums">{Math.round(escala * 100)}%</span>
        <Button
          variant="outline"
          size="icon"
          aria-label="Aumentar zoom"
          disabled={indiceEscala === ESCALAS.length - 1}
          onClick={() => setIndiceEscala((i) => i + 1)}
        >
          <ZoomIn />
        </Button>
        <div className="flex-1" />
        {urlObjeto && (
          <>
            <Button variant="ghost" size="sm" asChild>
              <a href={urlObjeto} target="_blank" rel="noreferrer">
                <ExternalLink /> Nova aba
              </a>
            </Button>
            <Button variant="ghost" size="sm" asChild>
              <a href={urlObjeto} download={`${titulo}.pdf`}>
                <Download /> Baixar
              </a>
            </Button>
          </>
        )}
      </div>
      <div ref={refArea} className="min-h-0 flex-1 overflow-auto bg-muted/40 p-4">
        {arquivo.isError ? (
          <ProblemaAlerta
            erro={arquivo.error}
            titulo="Não foi possível abrir o PDF"
            aoTentarDeNovo={() => void arquivo.refetch()}
          />
        ) : !arquivo.data ? (
          <Carregando texto="Baixando o PDF…" />
        ) : (
          <Document
            file={arquivo.data}
            options={OPCOES_PDF}
            loading={<Carregando texto="Abrindo o PDF…" />}
            error={<p className="p-4 text-sm text-destructive">O arquivo não pôde ser exibido.</p>}
            onLoadSuccess={({ numPages }) => {
              setTotal(numPages);
              setPagina((atual) => Math.min(atual, numPages));
            }}
            className="flex justify-center"
          >
            <Page
              pageNumber={pagina}
              width={larguraPagina}
              className="shadow-md"
              loading={<Carregando texto="Renderizando…" />}
            />
          </Document>
        )}
      </div>
    </div>
  );
}

function Carregando({ texto }: { texto: string }) {
  return (
    <div className="flex items-center justify-center gap-2 p-8 text-sm text-muted-foreground">
      <Loader2 className="size-4 animate-spin" /> {texto}
    </div>
  );
}
