import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { createColumnHelper } from "@tanstack/react-table";
import { Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { z } from "zod";

import {
  getListarParametrosQueryKey,
  getListarParametrosQueryOptions,
  getObterParametroQueryKey,
  useAlterarParametro,
  useExcluirParametro,
} from "@/api/gerado/parametros/parametros";
import { getListarFamiliasQueryOptions } from "@/api/gerado/familias/familias";
import { Idioma, type ParametroOut } from "@/api/gerado/modelos";
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
import { FormParametro } from "@/features/parametros/form-parametro";
import { formatarDataHora, formatarNumero } from "@/lib/formato";
import {
  ativoDaUrl,
  esquemaFiltroAtivo,
  FILTRO_ATIVO,
  IDIOMAS,
  ROTULO_FILTRO_ATIVO,
  ROTULO_IDIOMA,
  type FiltroAtivo,
} from "@/lib/rotulos";

const LIMITE = 20;
/** Limite máximo da API, usado só para resolver nomes nas colunas. */
const LIMITE_NOMES = 100;

const esquemaFiltros = z.object({
  busca: z.string().trim().max(100).optional().catch(undefined),
  id_familia: z.uuid().optional().catch(undefined),
  idioma: z.enum(Idioma).optional().catch(undefined),
  ativo: esquemaFiltroAtivo,
  offset: z.number().int().min(0).optional().catch(undefined),
});

export const Route = createFileRoute("/_app/parametros")({
  validateSearch: esquemaFiltros,
  component: PaginaParametros,
});

const coluna = createColumnHelper<ParametroOut>();

function PaginaParametros() {
  const filtros = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  const queryClient = useQueryClient();
  const podeEscrever = usePodeEscrever();
  const excluir = useExcluirParametro();
  const alterar = useAlterarParametro();
  const [formAberto, setFormAberto] = useState(false);
  const [editando, setEditando] = useState<ParametroOut | null>(null);
  const [excluindo, setExcluindo] = useState<ParametroOut | null>(null);
  const offset = filtros.offset ?? 0;

  const lista = useQuery({
    ...getListarParametrosQueryOptions({
      busca: filtros.busca,
      id_familia: filtros.id_familia,
      idioma: filtros.idioma,
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

  const desativar = async (parametro: ParametroOut) => {
    try {
      await alterar.mutateAsync({ idParametro: parametro.id_parametro, data: { ativo: false } });
      void queryClient.invalidateQueries({ queryKey: getListarParametrosQueryKey() });
      toast.success("Parâmetro desativado.");
    } catch (erro) {
      toast.error(mensagemDeErro(erro));
    }
  };

  const colunas = [
    coluna.accessor("codigo", {
      header: "Código",
      cell: ({ row }) => (
        <div className="min-w-32">
          <p className="font-mono text-sm">{row.original.codigo}</p>
          {row.original.nome && (
            <p className="line-clamp-1 text-xs text-muted-foreground">{row.original.nome}</p>
          )}
        </div>
      ),
    }),
    coluna.accessor("id_familia", {
      header: "Família",
      cell: ({ getValue }) => nomeFamilia(getValue()),
    }),
    coluna.accessor("descricao", {
      header: "Descrição",
      cell: ({ getValue }) => <span className="line-clamp-2 min-w-56 text-sm">{getValue()}</span>,
    }),
    coluna.display({
      id: "faixa",
      header: "Faixa",
      cell: ({ row }) => (
        <span className="text-sm whitespace-nowrap">
          {formatarNumero(row.original.valor_min)} – {formatarNumero(row.original.valor_max)}
          {row.original.unidade ? ` ${row.original.unidade}` : ""}
        </span>
      ),
    }),
    coluna.accessor("idioma", {
      header: "Idioma",
      cell: ({ getValue }) => ROTULO_IDIOMA[getValue()],
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
                  aria-label={`Editar ${row.original.codigo}`}
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
                  aria-label={`Excluir ${row.original.codigo}`}
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
        titulo="Parâmetros"
        descricao="Parâmetros de configuração por família, usados nas respostas do assistente."
        acoes={
          podeEscrever && (
            <Button
              onClick={() => {
                setEditando(null);
                setFormAberto(true);
              }}
            >
              <Plus /> Novo parâmetro
            </Button>
          )
        }
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <div className="grid gap-1.5 lg:col-span-2">
          <Label htmlFor="busca-parametros">Código ou descrição</Label>
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
              id="busca-parametros"
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
          <Label htmlFor="filtro-familia-par">Família</Label>
          <ComboboxFamilia
            id="filtro-familia-par"
            valor={filtros.id_familia}
            aoMudar={(id_familia) => {
              filtrar({ id_familia });
            }}
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="filtro-idioma-par">Idioma</Label>
          <SelectOpcoes
            id="filtro-idioma-par"
            valor={filtros.idioma}
            aoMudar={(idioma) => {
              filtrar({ idioma });
            }}
            opcoes={IDIOMAS}
            rotulos={ROTULO_IDIOMA}
            rotuloTodos="Todos"
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="filtro-ativo-par">Situação</Label>
          <SelectOpcoes
            id="filtro-ativo-par"
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
          idLinha={(p) => p.id_parametro}
          mensagemVazia="Nenhum parâmetro com esses filtros."
          aoMudarOffset={(novo) => {
            void navigate({ search: (atual) => ({ ...atual, offset: novo || undefined }) });
          }}
          aoClicarLinha={
            podeEscrever
              ? (p) => {
                  setEditando(p);
                  setFormAberto(true);
                }
              : undefined
          }
        />
      )}

      <FormParametro
        aberto={formAberto}
        aoMudar={setFormAberto}
        parametro={editando}
        aoSalvar={() => {
          void lista.refetch();
        }}
      />

      <ConfirmarExclusao
        aberto={excluindo !== null}
        aoMudar={(aberto) => {
          if (!aberto) setExcluindo(null);
        }}
        titulo="Excluir parâmetro?"
        descricao={
          <>
            O parâmetro <strong>{excluindo?.codigo}</strong> será removido definitivamente.
          </>
        }
        aoConfirmar={async () => {
          if (!excluindo) return;
          try {
            await excluir.mutateAsync({ idParametro: excluindo.id_parametro });
            queryClient.removeQueries({ queryKey: getObterParametroQueryKey(excluindo.id_parametro) });
            void queryClient.invalidateQueries({ queryKey: getListarParametrosQueryKey() });
            toast.success("Parâmetro excluído.");
            setExcluindo(null);
          } catch (erro) {
            if (ehProblema(erro, 409)) {
              const alvo = excluindo;
              setExcluindo(null);
              toast.error("Parâmetro com vínculos não pode ser excluído.", {
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
