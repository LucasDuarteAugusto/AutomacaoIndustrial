import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { createColumnHelper } from "@tanstack/react-table";
import { Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { z } from "zod";

import {
  getListarFabricantesQueryKey,
  getListarFabricantesQueryOptions,
  getObterFabricanteQueryKey,
  useAlterarFabricante,
  useExcluirFabricante,
} from "@/api/gerado/fabricantes/fabricantes";
import type { FabricanteOut } from "@/api/gerado/modelos";
import { ehProblema, mensagemDeErro } from "@/api/problema";
import { BadgeAtivo } from "@/components/badge-ativo";
import { CabecalhoPagina } from "@/components/cabecalho-pagina";
import { ConfirmarExclusao } from "@/components/confirmar-exclusao";
import { ProblemaAlerta } from "@/components/problema-alerta";
import { SelectOpcoes } from "@/components/select-opcoes";
import { TabelaDados } from "@/components/tabela-dados";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { usePodeEscrever } from "@/features/auth/sessao";
import { FormFabricante } from "@/features/fabricantes/form-fabricante";
import { formatarDataHora } from "@/lib/formato";
import {
  ativoDaUrl,
  esquemaFiltroAtivo,
  FILTRO_ATIVO,
  ROTULO_FILTRO_ATIVO,
  type FiltroAtivo,
} from "@/lib/rotulos";

const LIMITE = 20;

const esquemaFiltros = z.object({
  busca: z.string().trim().max(100).optional().catch(undefined),
  ativo: esquemaFiltroAtivo,
  offset: z.number().int().min(0).optional().catch(undefined),
});

export const Route = createFileRoute("/_app/fabricantes")({
  validateSearch: esquemaFiltros,
  component: PaginaFabricantes,
});

const coluna = createColumnHelper<FabricanteOut>();

function PaginaFabricantes() {
  const filtros = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  const queryClient = useQueryClient();
  const podeEscrever = usePodeEscrever();
  const excluir = useExcluirFabricante();
  const alterar = useAlterarFabricante();
  const [formAberto, setFormAberto] = useState(false);
  const [editando, setEditando] = useState<FabricanteOut | null>(null);
  const [excluindo, setExcluindo] = useState<FabricanteOut | null>(null);
  const offset = filtros.offset ?? 0;

  const lista = useQuery({
    ...getListarFabricantesQueryOptions({
      busca: filtros.busca,
      ativo: ativoDaUrl(filtros.ativo),
      offset,
      limit: LIMITE,
    }),
    placeholderData: (anterior) => anterior,
  });

  const filtrar = (parcial: Partial<z.infer<typeof esquemaFiltros>>) => {
    void navigate({ search: (atual) => ({ ...atual, ...parcial, offset: undefined }), replace: true });
  };

  const desativar = async (fabricante: FabricanteOut) => {
    try {
      await alterar.mutateAsync({ idFabricante: fabricante.id_fabricante, data: { ativo: false } });
      void queryClient.invalidateQueries({ queryKey: getListarFabricantesQueryKey() });
      toast.success("Fabricante desativado.");
    } catch (erro) {
      toast.error(mensagemDeErro(erro));
    }
  };

  const colunas = [
    coluna.accessor("nome", {
      header: "Nome",
      cell: ({ row }) => (
        <div className="min-w-40">
          <p className="font-medium">{row.original.nome}</p>
          {row.original.site && (
            <a
              href={row.original.site}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-muted-foreground hover:underline"
              onClick={(e) => {
                e.stopPropagation();
              }}
            >
              {row.original.site}
            </a>
          )}
        </div>
      ),
    }),
    coluna.accessor("ativo", {
      header: "Situação",
      cell: ({ getValue }) => <BadgeAtivo ativo={getValue()} />,
    }),
    coluna.accessor("updated_at", {
      header: "Atualizado",
      cell: ({ getValue }) => <span className="whitespace-nowrap">{formatarDataHora(getValue())}</span>,
    }),
    ...(podeEscrever
      ? [
          coluna.display({
            id: "acoes",
            header: "",
            cell: ({ row }) => (
              <div className="flex justify-end gap-1">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  aria-label={`Editar ${row.original.nome}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setEditando(row.original);
                    setFormAberto(true);
                  }}
                >
                  <Pencil />
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  aria-label={`Excluir ${row.original.nome}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setExcluindo(row.original);
                  }}
                >
                  <Trash2 />
                </Button>
              </div>
            ),
          }),
        ]
      : []),
  ];

  return (
    <div className="space-y-4">
      <CabecalhoPagina
        titulo="Fabricantes"
        descricao="Marcas e fornecedores das famílias de equipamento."
        acoes={
          podeEscrever && (
            <Button
              onClick={() => {
                setEditando(null);
                setFormAberto(true);
              }}
            >
              <Plus /> Novo fabricante
            </Button>
          )
        }
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="grid gap-1.5 lg:col-span-2">
          <Label htmlFor="busca-fabricantes">Nome</Label>
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
              id="busca-fabricantes"
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
          <Label htmlFor="filtro-ativo-fab">Situação</Label>
          <SelectOpcoes
            id="filtro-ativo-fab"
            valor={filtros.ativo}
            aoMudar={(ativo: FiltroAtivo | undefined) => {
              filtrar({ ativo });
            }}
            opcoes={FILTRO_ATIVO}
            rotulos={ROTULO_FILTRO_ATIVO}
            rotuloTodos="Todas"
          />
        </div>
      </div>

      {lista.isError ? (
        <ProblemaAlerta erro={lista.error} aoTentarDeNovo={() => void lista.refetch()} />
      ) : (
        <TabelaDados
          colunas={colunas}
          dados={lista.data?.items}
          total={lista.data?.total ?? 0}
          limit={LIMITE}
          offset={offset}
          carregando={lista.isFetching && !lista.data}
          idLinha={(f) => f.id_fabricante}
          mensagemVazia="Nenhum fabricante com esses filtros."
          aoMudarOffset={(novo) => {
            void navigate({ search: (atual) => ({ ...atual, offset: novo || undefined }) });
          }}
          aoClicarLinha={
            podeEscrever
              ? (f) => {
                  setEditando(f);
                  setFormAberto(true);
                }
              : undefined
          }
        />
      )}

      <FormFabricante
        aberto={formAberto}
        aoMudar={setFormAberto}
        fabricante={editando}
        aoSalvar={() => {
          void lista.refetch();
        }}
      />

      <ConfirmarExclusao
        aberto={excluindo !== null}
        aoMudar={(aberto) => {
          if (!aberto) setExcluindo(null);
        }}
        titulo="Excluir fabricante?"
        descricao={
          <>
            <strong>{excluindo?.nome}</strong> será removido. Famílias vinculadas impedem a exclusão.
          </>
        }
        aoConfirmar={async () => {
          if (!excluindo) return;
          try {
            await excluir.mutateAsync({ idFabricante: excluindo.id_fabricante });
            queryClient.removeQueries({ queryKey: getObterFabricanteQueryKey(excluindo.id_fabricante) });
            void queryClient.invalidateQueries({ queryKey: getListarFabricantesQueryKey() });
            toast.success("Fabricante excluído.");
            setExcluindo(null);
          } catch (erro) {
            if (ehProblema(erro, 409)) {
              const alvo = excluindo;
              setExcluindo(null);
              toast.error("Fabricante com vínculos não pode ser excluído.", {
                action: {
                  label: "Desativar",
                  onClick: () => void desativar(alvo),
                },
              });
              return;
            }
            toast.error(mensagemDeErro(erro));
            throw erro;
          }
        }}
      />
    </div>
  );
}
