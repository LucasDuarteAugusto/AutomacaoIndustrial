import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Search } from "lucide-react";
import { useState } from "react";
import { z } from "zod";

import { buscar } from "@/api/gerado/busca/busca";
import type { BuscaRequest, TrechoBuscaOut } from "@/api/gerado/modelos";
import { CabecalhoPagina } from "@/components/cabecalho-pagina";
import { ProblemaAlerta } from "@/components/problema-alerta";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { type PdfAberto, VisualizadorPdf } from "@/components/visualizador-pdf";
import { ResultadoTrecho } from "@/features/busca/resultado-trecho";
import { esquemaContexto, filtrosParaRequisicao } from "@/features/contexto/esquema";
import { FiltrosContexto } from "@/features/contexto/filtros-contexto";

const LIMITE_PADRAO = 10;

const esquemaBusca = esquemaContexto.extend({
  q: z.string().trim().max(2000).optional().catch(undefined),
  limit: z.number().int().min(1).max(50).optional().catch(undefined),
});

export const Route = createFileRoute("/_app/busca")({
  validateSearch: esquemaBusca,
  component: PaginaBusca,
});

function PaginaBusca() {
  const { q, limit, ...contexto } = Route.useSearch();
  const navigate = Route.useNavigate();
  const [pdf, setPdf] = useState<PdfAberto | null>(null);
  const limite = limit ?? LIMITE_PADRAO;

  const requisicao: BuscaRequest = { consulta: q ?? "", limit: limite, ...filtrosParaRequisicao(contexto) };
  const resultado = useQuery({
    queryKey: ["busca", requisicao],
    queryFn: ({ signal }) => buscar(requisicao, { signal }),
    enabled: !!q,
    staleTime: 5 * 60_000,
  });

  function abrirPdf(trecho: TrechoBuscaOut) {
    setPdf({
      idDocumento: trecho.id_documento,
      titulo: trecho.titulo_documento,
      paginaInicial: trecho.pagina,
      rotuloPagina: trecho.pagina !== null ? `Aberto na página ${trecho.pagina}` : undefined,
    });
  }

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <CabecalhoPagina
        titulo="Busca em documentos"
        descricao="Busca híbrida (significado + palavras exatas) nos trechos dos manuais indexados. Use códigos como p1120 ou F07801."
      />

      <form
        role="search"
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          const valor = new FormData(e.currentTarget).get("q");
          const texto = typeof valor === "string" ? valor.trim() : "";
          void navigate({ search: (atual) => ({ ...atual, q: texto || undefined }) });
        }}
      >
        <label htmlFor="consulta" className="sr-only">
          Consulta
        </label>
        <Input
          key={q ?? ""}
          id="consulta"
          name="q"
          type="search"
          defaultValue={q ?? ""}
          maxLength={2000}
          placeholder="Ex.: tempo de rampa de aceleração p1120"
          autoFocus
          className="flex-1"
        />
        <Button type="submit">
          <Search /> Buscar
        </Button>
      </form>

      <FiltrosContexto
        contexto={contexto}
        aoMudar={(novo) => {
          void navigate({ search: { ...novo, q, limit }, replace: true });
        }}
      />

      {!q && (
        <p className="py-8 text-center text-sm text-muted-foreground">
          Digite o que procura. Os filtros de contexto ajudam quando o mesmo assunto aparece em vários
          equipamentos.
        </p>
      )}

      {q && resultado.isPending && (
        <div className="space-y-3" role="status" aria-label="Buscando">
          {Array.from({ length: 3 }, (_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      )}

      {resultado.isError && (
        <ProblemaAlerta
          erro={resultado.error}
          titulo="A busca falhou"
          aoTentarDeNovo={() => void resultado.refetch()}
        />
      )}

      {resultado.data && (
        <section aria-label="Resultados" className="space-y-3">
          <p className="text-sm text-muted-foreground" aria-live="polite">
            {resultado.data.total === 0
              ? "Nenhum trecho encontrado. Tente outras palavras ou remova filtros."
              : `${resultado.data.total} trecho${resultado.data.total === 1 ? "" : "s"} encontrado${resultado.data.total === 1 ? "" : "s"}.`}
          </p>
          {resultado.data.items.map((trecho, i) => (
            <ResultadoTrecho
              key={trecho.id_trecho}
              trecho={trecho}
              posicao={i + 1}
              consulta={resultado.data.consulta}
              aoAbrirPdf={abrirPdf}
            />
          ))}
          {resultado.data.items.length >= limite && limite < 50 && (
            <div className="flex justify-center">
              <Button
                variant="outline"
                onClick={() => {
                  void navigate({ search: (atual) => ({ ...atual, limit: Math.min(50, limite + 10) }) });
                }}
              >
                Mostrar mais resultados
              </Button>
            </div>
          )}
        </section>
      )}

      <VisualizadorPdf
        pdf={pdf}
        aoFechar={() => {
          setPdf(null);
        }}
      />
    </div>
  );
}
