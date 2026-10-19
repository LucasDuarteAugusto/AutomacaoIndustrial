import { createFileRoute } from "@tanstack/react-router";

import { CabecalhoPagina } from "@/components/cabecalho-pagina";

export const Route = createFileRoute("/_app/documentos/$idDocumento")({
  component: () => <CabecalhoPagina titulo="Documento" />,
});
