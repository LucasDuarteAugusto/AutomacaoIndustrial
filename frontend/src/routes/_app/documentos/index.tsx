import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { createColumnHelper } from "@tanstack/react-table";
import { Plus, Search } from "lucide-react";
import { useState } from "react";
import { z } from "zod";

import { getListarDocumentosQueryOptions } from "@/api/gerado/documentos/documentos";
import { Idioma, StatusProcessamento, TipoDocumento, type DocumentoOut } from "@/api/gerado/modelos";
import { CabecalhoPagina } from "@/components/cabecalho-pagina";
import { ProblemaAlerta } from "@/components/problema-alerta";
import { SelectOpcoes } from "@/components/select-opcoes";
import { StatusBadge } from "@/components/status-badge";
import { TabelaDados } from "@/components/tabela-dados";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { usePodeEscrever } from "@/features/auth/sessao";
import { ComboboxFamilia } from "@/features/catalogo/comboboxes";
import { estaProcessando } from "@/features/documentos/cache";
import { FormNovoDocumento } from "@/features/documentos/form-novo-documento";
import { formatarDataHora } from "@/lib/formato";
import {
  IDIOMAS,
  ROTULO_IDIOMA,
  ROTULO_STATUS,
  ROTULO_TIPO_DOCUMENTO,
  STATUS_PROCESSAMENTO,
  TIPOS_DOCUMENTO,
} from "@/lib/rotulos";

const LIMITE = 20;

const esquemaFiltros = z.object({
  busca: z.string().trim().max(100).optional().catch(undefined),
  tipo_documento: z.enum(TipoDocumento).optional().catch(undefined),
  idioma: z.enum(Idioma).optional().catch(undefined),
  status_processamento: z.enum(StatusProcessamento).optional().catch(undefined),
  id_familia: z.uuid().optional().catch(undefined),
  offset: z.number().int().min(0).optional().catch(undefined),
});

export const Route = createFileRoute("/_app/documentos/")({
  validateSearch: esquemaFiltros,
  component: PaginaDocumentos,
});

const coluna = createColumnHelper<DocumentoOut>();

const COLUNAS = [
  coluna.accessor("titulo", {
    header: "Título",
    cell: ({ row }) => (
      <div className="min-w-48">
        <Link
          to="/documentos/$idDocumento"
          params={{ idDocumento: row.original.id_documento }}
          className="font-medium hover:underline"
          onClick={(e) => {
            e.stopPropagation();
          }}
        >
          {row.original.titulo}
        </Link>
        {row.original.codigo_documento && (
          <p className="font-mono text-xs text-muted-foreground">{row.original.codigo_documento}</p>
        )}
      </div>
    ),
  }),
  coluna.accessor("tipo_documento", {
    header: "Tipo",
    cell: ({ getValue }) => ROTULO_TIPO_DOCUMENTO[getValue()],
  }),
  coluna.accessor("idioma", { header: "Idioma", cell: ({ getValue }) => ROTULO_IDIOMA[getValue()] }),
  coluna.accessor("familias", {
    header: "Famílias",
    cell: ({ getValue }) => (
      <span className="line-clamp-2 text-sm">
        {getValue()
          .map((f) => f.nome)
          .join(", ") || "—"}
      </span>
    ),
  }),
  coluna.accessor("status_processamento", {
    header: "Status",
    cell: ({ getValue }) => <StatusBadge status={getValue()} />,
  }),
  coluna.accessor("updated_at", {
    header: "Atualizado",
    cell: ({ getValue }) => <span className="whitespace-nowrap">{formatarDataHora(getValue())}</span>,
  }),
];

function PaginaDocumentos() {
  const filtros = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  const podeEscrever = usePodeEscrever();
  const [criando, setCriando] = useState(false);
  const offset = filtros.offset ?? 0;

  const lista = useQuery({
    ...getListarDocumentosQueryOptions({ ...filtros, offset, limit: LIMITE }),
    placeholderData: (anterior) => anterior,
    refetchInterval: (consulta) => (consulta.state.data?.items.some(estaProcessando) ? 5000 : false),
  });

  const filtrar = (parcial: Partial<z.infer<typeof esquemaFiltros>>) => {
    void navigate({ search: (atual) => ({ ...atual, ...parcial, offset: undefined }), replace: true });
  };

  return (
    <div className="space-y-4">
      <CabecalhoPagina
        titulo="Documentos"
        descricao="Manuais, listas de parâmetros e datasheets. Documentos indexados entram na busca e no assistente."
        acoes={
          podeEscrever && (
            <Button
              onClick={() => {
                setCriando(true);
              }}
            >
              <Plus /> Novo documento
            </Button>
          )
        }
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <div className="grid gap-1.5 lg:col-span-2">
          <Label htmlFor="busca-documentos">Título ou código</Label>
          <form
            role="search"
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              const valor = new FormData(e.currentTarget).get("busca");
              filtrar({ busca: typeof valor === "string" && valor.trim() ? valor.trim() : undefined });
            }}
          >
            <Input
              key={filtros.busca ?? ""}
              id="busca-documentos"
              name="busca"
              type="search"
              defaultValue={filtros.busca ?? ""}
              maxLength={100}
              placeholder="Buscar…"
            />
            <Button type="submit" variant="outline" size="icon" aria-label="Buscar">
              <Search />
            </Button>
          </form>
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="filtro-tipo-doc">Tipo</Label>
          <SelectOpcoes
            id="filtro-tipo-doc"
            valor={filtros.tipo_documento}
            aoMudar={(tipo_documento) => {
              filtrar({ tipo_documento });
            }}
            opcoes={TIPOS_DOCUMENTO}
            rotulos={ROTULO_TIPO_DOCUMENTO}
            rotuloTodos="Todos"
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="filtro-status-doc">Status</Label>
          <SelectOpcoes
            id="filtro-status-doc"
            valor={filtros.status_processamento}
            aoMudar={(status_processamento) => {
              filtrar({ status_processamento });
            }}
            opcoes={STATUS_PROCESSAMENTO}
            rotulos={ROTULO_STATUS}
            rotuloTodos="Todos"
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="filtro-idioma-doc">Idioma</Label>
          <SelectOpcoes
            id="filtro-idioma-doc"
            valor={filtros.idioma}
            aoMudar={(idioma) => {
              filtrar({ idioma });
            }}
            opcoes={IDIOMAS}
            rotulos={ROTULO_IDIOMA}
            rotuloTodos="Todos"
          />
        </div>
        <div className="grid gap-1.5 lg:col-span-2">
          <Label htmlFor="filtro-familia-doc">Família</Label>
          <ComboboxFamilia
            id="filtro-familia-doc"
            valor={filtros.id_familia}
            aoMudar={(id_familia) => {
              filtrar({ id_familia });
            }}
          />
        </div>
      </div>

      {lista.isError ? (
        <ProblemaAlerta erro={lista.error} aoTentarDeNovo={() => void lista.refetch()} />
      ) : (
        <TabelaDados
          colunas={COLUNAS}
          dados={lista.data?.items}
          total={lista.data?.total ?? 0}
          limit={LIMITE}
          offset={offset}
          carregando={lista.isFetching && !lista.data}
          idLinha={(d) => d.id_documento}
          mensagemVazia="Nenhum documento com esses filtros."
          aoMudarOffset={(novo) => {
            void navigate({ search: (atual) => ({ ...atual, offset: novo || undefined }) });
          }}
          aoClicarLinha={(d) => {
            void navigate({ to: "/documentos/$idDocumento", params: { idDocumento: d.id_documento } });
          }}
        />
      )}

      <FormNovoDocumento
        aberto={criando}
        aoMudar={setCriando}
        aoCriar={(documento) => {
          setCriando(false);
          void navigate({ to: "/documentos/$idDocumento", params: { idDocumento: documento.id_documento } });
        }}
      />
    </div>
  );
}
