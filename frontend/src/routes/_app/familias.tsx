import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { createColumnHelper } from "@tanstack/react-table";
import { Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { z } from "zod";

import { getListarFabricantesQueryOptions } from "@/api/gerado/fabricantes/fabricantes";
import {
  getListarFamiliasQueryKey,
  getListarFamiliasQueryOptions,
  getObterFamiliaQueryKey,
  useAlterarFamilia,
  useExcluirFamilia,
} from "@/api/gerado/familias/familias";
import type { FamiliaOut } from "@/api/gerado/modelos";
import { getListarTiposQueryOptions } from "@/api/gerado/tipos-equipamento/tipos-equipamento";
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
import { ComboboxFabricante, ComboboxTipoEquipamento } from "@/features/catalogo/comboboxes";
import { FormFamilia } from "@/features/familias/form-familia";
import { formatarDataHora } from "@/lib/formato";
import {
  ativoDaUrl,
  esquemaFiltroAtivo,
  FILTRO_ATIVO,
  ROTULO_FILTRO_ATIVO,
  type FiltroAtivo,
} from "@/lib/rotulos";

const LIMITE = 20;
/** Limite máximo da API, usado só para resolver nomes nas colunas. */
const LIMITE_NOMES = 100;

const esquemaFiltros = z.object({
  busca: z.string().trim().max(100).optional().catch(undefined),
  id_fabricante: z.uuid().optional().catch(undefined),
  id_tipo_equipamento: z.uuid().optional().catch(undefined),
  ativo: esquemaFiltroAtivo,
  offset: z.number().int().min(0).optional().catch(undefined),
});

export const Route = createFileRoute("/_app/familias")({
  validateSearch: esquemaFiltros,
  component: PaginaFamilias,
});

const coluna = createColumnHelper<FamiliaOut>();

function PaginaFamilias() {
  const filtros = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  const queryClient = useQueryClient();
  const podeEscrever = usePodeEscrever();
  const excluir = useExcluirFamilia();
  const alterar = useAlterarFamilia();
  const [formAberto, setFormAberto] = useState(false);
  const [editando, setEditando] = useState<FamiliaOut | null>(null);
  const [excluindo, setExcluindo] = useState<FamiliaOut | null>(null);
  const offset = filtros.offset ?? 0;

  const lista = useQuery({
    ...getListarFamiliasQueryOptions({
      busca: filtros.busca,
      id_fabricante: filtros.id_fabricante,
      id_tipo_equipamento: filtros.id_tipo_equipamento,
      ativo: ativoDaUrl(filtros.ativo),
      offset,
      limit: LIMITE,
    }),
    placeholderData: (anterior) => anterior,
  });

  const fabricantes = useQuery(getListarFabricantesQueryOptions({ limit: LIMITE_NOMES }));
  const tipos = useQuery(getListarTiposQueryOptions({ limit: LIMITE_NOMES }));

  const nomeFabricante = (id: string) =>
    fabricantes.data?.items.find((f) => f.id_fabricante === id)?.nome ?? "—";
  const nomeTipo = (id: string) => tipos.data?.items.find((t) => t.id_tipo_equipamento === id)?.nome ?? "—";

  const filtrar = (parcial: Partial<z.infer<typeof esquemaFiltros>>) => {
    void navigate({ search: (atual) => ({ ...atual, ...parcial, offset: undefined }), replace: true });
  };

  const desativar = async (familia: FamiliaOut) => {
    try {
      await alterar.mutateAsync({ idFamilia: familia.id_familia, data: { ativo: false } });
      void queryClient.invalidateQueries({ queryKey: getListarFamiliasQueryKey() });
      toast.success("Família desativada.");
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
          {row.original.descricao && (
            <p className="line-clamp-1 text-xs text-muted-foreground">{row.original.descricao}</p>
          )}
        </div>
      ),
    }),
    coluna.accessor("id_fabricante", {
      header: "Fabricante",
      cell: ({ getValue }) => nomeFabricante(getValue()),
    }),
    coluna.accessor("id_tipo_equipamento", {
      header: "Tipo",
      cell: ({ getValue }) => nomeTipo(getValue()),
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
        titulo="Famílias"
        descricao="Linhas de produto de um fabricante, com o tipo de acionamento."
        acoes={
          podeEscrever && (
            <Button
              onClick={() => {
                setEditando(null);
                setFormAberto(true);
              }}
            >
              <Plus /> Nova família
            </Button>
          )
        }
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <div className="grid gap-1.5 lg:col-span-2">
          <Label htmlFor="busca-familias">Nome</Label>
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
              id="busca-familias"
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
          <Label htmlFor="filtro-fabricante-fam">Fabricante</Label>
          <ComboboxFabricante
            id="filtro-fabricante-fam"
            valor={filtros.id_fabricante}
            aoMudar={(id_fabricante) => {
              filtrar({ id_fabricante });
            }}
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="filtro-tipo-fam">Tipo</Label>
          <ComboboxTipoEquipamento
            id="filtro-tipo-fam"
            valor={filtros.id_tipo_equipamento}
            aoMudar={(id_tipo_equipamento) => {
              filtrar({ id_tipo_equipamento });
            }}
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="filtro-ativo-fam">Situação</Label>
          <SelectOpcoes
            id="filtro-ativo-fam"
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
          idLinha={(f) => f.id_familia}
          mensagemVazia="Nenhuma família com esses filtros."
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

      <FormFamilia
        aberto={formAberto}
        aoMudar={setFormAberto}
        familia={editando}
        aoSalvar={() => {
          void lista.refetch();
        }}
      />

      <ConfirmarExclusao
        aberto={excluindo !== null}
        aoMudar={(aberto) => {
          if (!aberto) setExcluindo(null);
        }}
        titulo="Excluir família?"
        descricao={
          <>
            <strong>{excluindo?.nome}</strong> será removida. Equipamentos e documentos vinculados impedem a
            exclusão.
          </>
        }
        aoConfirmar={async () => {
          if (!excluindo) return;
          try {
            await excluir.mutateAsync({ idFamilia: excluindo.id_familia });
            queryClient.removeQueries({ queryKey: getObterFamiliaQueryKey(excluindo.id_familia) });
            void queryClient.invalidateQueries({ queryKey: getListarFamiliasQueryKey() });
            toast.success("Família excluída.");
            setExcluindo(null);
          } catch (erro) {
            if (ehProblema(erro, 409)) {
              const alvo = excluindo;
              setExcluindo(null);
              toast.error("Família com vínculos não pode ser excluída.", {
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
