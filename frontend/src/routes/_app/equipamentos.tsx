import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { createColumnHelper } from "@tanstack/react-table";
import { Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { z } from "zod";

import {
  getListarEquipamentosQueryKey,
  getListarEquipamentosQueryOptions,
  getObterEquipamentoQueryKey,
  useAlterarEquipamento,
  useExcluirEquipamento,
} from "@/api/gerado/equipamentos/equipamentos";
import { getListarFamiliasQueryOptions } from "@/api/gerado/familias/familias";
import type { EquipamentoOut } from "@/api/gerado/modelos";
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
import { ComboboxFamilia } from "@/features/catalogo/comboboxes";
import { FormEquipamento } from "@/features/equipamentos/form-equipamento";
import { formatarDataHora, formatarNumero } from "@/lib/formato";
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
  id_familia: z.uuid().optional().catch(undefined),
  ativo: esquemaFiltroAtivo,
  offset: z.number().int().min(0).optional().catch(undefined),
});

export const Route = createFileRoute("/_app/equipamentos")({
  validateSearch: esquemaFiltros,
  component: PaginaEquipamentos,
});

const coluna = createColumnHelper<EquipamentoOut>();

function PaginaEquipamentos() {
  const filtros = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  const queryClient = useQueryClient();
  const podeEscrever = usePodeEscrever();
  const excluir = useExcluirEquipamento();
  const alterar = useAlterarEquipamento();
  const [formAberto, setFormAberto] = useState(false);
  const [editando, setEditando] = useState<EquipamentoOut | null>(null);
  const [excluindo, setExcluindo] = useState<EquipamentoOut | null>(null);
  const offset = filtros.offset ?? 0;

  const lista = useQuery({
    ...getListarEquipamentosQueryOptions({
      busca: filtros.busca,
      id_familia: filtros.id_familia,
      ativo: ativoDaUrl(filtros.ativo),
      offset,
      limit: LIMITE,
    }),
    placeholderData: (anterior) => anterior,
  });

  const familias = useQuery(getListarFamiliasQueryOptions({ limit: LIMITE_NOMES }));
  const nomeFamilia = (id: string) => familias.data?.items.find((f) => f.id_familia === id)?.nome ?? "—";

  const filtrar = (parcial: Partial<z.infer<typeof esquemaFiltros>>) => {
    void navigate({ search: (atual) => ({ ...atual, ...parcial, offset: undefined }), replace: true });
  };

  const desativar = async (equipamento: EquipamentoOut) => {
    try {
      await alterar.mutateAsync({ idEquipamento: equipamento.id_equipamento, data: { ativo: false } });
      void queryClient.invalidateQueries({ queryKey: getListarEquipamentosQueryKey() });
      toast.success("Equipamento desativado.");
    } catch (erro) {
      toast.error(mensagemDeErro(erro));
    }
  };

  const colunas = [
    coluna.accessor("codigo_pedido", {
      header: "Código",
      cell: ({ getValue }) => <span className="font-mono text-sm">{getValue()}</span>,
    }),
    coluna.accessor("nome", {
      header: "Nome",
      cell: ({ getValue }) => <span className="min-w-40 font-medium">{getValue()}</span>,
    }),
    coluna.accessor("id_familia", {
      header: "Família",
      cell: ({ getValue }) => nomeFamilia(getValue()),
    }),
    coluna.display({
      id: "nominais",
      header: "Dados nominais",
      cell: ({ row }) => (
        <div className="text-sm whitespace-nowrap">
          <p>
            {formatarNumero(row.original.tensao_nominal_v, "V")} /{" "}
            {formatarNumero(row.original.corrente_nominal_a, "A")}
          </p>
          <p className="text-xs text-muted-foreground">{formatarNumero(row.original.potencia_kw, "kW")}</p>
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
                  aria-label={`Editar ${row.original.codigo_pedido}`}
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
                  aria-label={`Excluir ${row.original.codigo_pedido}`}
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
        titulo="Equipamentos"
        descricao="Modelos de acionamento de uma família, com os dados nominais de placa."
        acoes={
          podeEscrever && (
            <Button
              onClick={() => {
                setEditando(null);
                setFormAberto(true);
              }}
            >
              <Plus /> Novo equipamento
            </Button>
          )
        }
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="grid gap-1.5 lg:col-span-2">
          <Label htmlFor="busca-equipamentos">Código ou nome</Label>
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
              id="busca-equipamentos"
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
          <Label htmlFor="filtro-familia-eq">Família</Label>
          <ComboboxFamilia
            id="filtro-familia-eq"
            valor={filtros.id_familia}
            aoMudar={(id_familia) => {
              filtrar({ id_familia });
            }}
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="filtro-ativo-eq">Situação</Label>
          <SelectOpcoes
            id="filtro-ativo-eq"
            valor={filtros.ativo}
            aoMudar={(ativo: FiltroAtivo | undefined) => {
              filtrar({ ativo });
            }}
            opcoes={FILTRO_ATIVO}
            rotulos={ROTULO_FILTRO_ATIVO}
            rotuloTodos="Todos"
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
          idLinha={(e) => e.id_equipamento}
          mensagemVazia="Nenhum equipamento com esses filtros."
          aoMudarOffset={(novo) => {
            void navigate({ search: (atual) => ({ ...atual, offset: novo || undefined }) });
          }}
          aoClicarLinha={
            podeEscrever
              ? (e) => {
                  setEditando(e);
                  setFormAberto(true);
                }
              : undefined
          }
        />
      )}

      <FormEquipamento
        aberto={formAberto}
        aoMudar={setFormAberto}
        equipamento={editando}
        aoSalvar={() => {
          void lista.refetch();
        }}
      />

      <ConfirmarExclusao
        aberto={excluindo !== null}
        aoMudar={(aberto) => {
          if (!aberto) setExcluindo(null);
        }}
        titulo="Excluir equipamento?"
        descricao={
          <>
            <strong>{excluindo?.codigo_pedido}</strong> será removido. Documentos vinculados impedem a
            exclusão.
          </>
        }
        aoConfirmar={async () => {
          if (!excluindo) return;
          try {
            await excluir.mutateAsync({ idEquipamento: excluindo.id_equipamento });
            queryClient.removeQueries({ queryKey: getObterEquipamentoQueryKey(excluindo.id_equipamento) });
            void queryClient.invalidateQueries({ queryKey: getListarEquipamentosQueryKey() });
            toast.success("Equipamento excluído.");
            setExcluindo(null);
          } catch (erro) {
            if (ehProblema(erro, 409)) {
              const alvo = excluindo;
              setExcluindo(null);
              toast.error("Equipamento com vínculos não pode ser excluído.", {
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
