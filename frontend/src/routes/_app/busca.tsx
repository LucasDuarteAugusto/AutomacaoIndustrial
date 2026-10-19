import { createFileRoute } from "@tanstack/react-router";

import { CabecalhoPagina } from "@/components/cabecalho-pagina";

export const Route = createFileRoute("/_app/busca")({
  component: () => <CabecalhoPagina titulo="Busca" />,
});
