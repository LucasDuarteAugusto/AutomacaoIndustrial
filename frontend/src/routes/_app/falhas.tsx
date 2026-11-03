import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { createColumnHelper } from "@tanstack/react-table";
import { Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { z } from "zod";

import { getListarFamiliasQueryOptions } from "@/api/gerado/familias/familias";
import {
  getListarFalhasQueryKey,
  getListarFalhasQueryOptions,
  getObterFalhaQueryKey,
  useAlterarFalha,
  useExcluirFalha,
} from "@/api/gerado/falhas/falhas";
import { Idioma, TipoFalha, type FalhaOut } from "@/api/gerado/modelos";
import { ehProblema, mensagemDeErro } from "@/api/problema";
import { BadgeAtivo } from "@/components/badge-ativo";
import { CabecalhoPagina } from "@/components/cabecalho-pagina";
import { ConfirmarExclusao } from "@/components/confirmar-exclusao";
import { ProblemaAlerta } from "@/components/problema-alerta";
import { SelectOpcoes } from "@/components/select-opcoes";
import { TabelaDados } from "@/components/tabela-dados";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { usePodeEscrever } from "@/features/auth/sessao";
import { ComboboxFamilia } from "@/features/catalogo/comboboxes";
import { FormFalha } from "@/features/falhas/form-falha";
import { formatarDataHora } from "@/lib/formato";
import {
  ativoDaUrl,
  esquemaFiltroAtivo,
  FILTRO_ATIVO,
  IDIOMAS,
  ROTULO_FILTRO_ATIVO,
  ROTULO_IDIOMA,
  ROTULO_TIPO_FALHA,
  TIPOS_FALHA,
  type FiltroAtivo,
} from "@/lib/rotulos";

const LIMITE = 20;
/** Limite máximo da API, usado só para resolver nomes nas colunas. */
const LIMITE_NOMES = 100;

const esquemaFiltros = z.object({
  busca: z.string().trim().max(100).optional().catch(undefined),
  id_familia: z.uuid().optional().catch(undefined),
  tipo: z.enum(TipoFalha).optional().catch(undefined),
  idioma: z.enum(Idioma).optional().catch(undefined),
  ativo: esquemaFiltroAtivo,
  offset: z.number().int().min(0).optional().catch(undefined),
});

export const Route = createFileRoute("/_app/falhas")({
  validateSearch: esquemaFiltros,
  component: PaginaFalhas,
});

const coluna = createColumnHelper<FalhaOut>();

function PaginaFalhas() {
  const filtros = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  const queryClient = useQueryClient();
  const podeEscrever = usePodeEscrever();
  const excluir = useExcluirFalha();
  const alterar = useAlterarFalha();
  const [formAberto, setFormAberto] = useState(false);
  const [editando, setEditando] = useState<FalhaOut | null>(null);
  const [excluindo, setExcluindo] = useState<FalhaOut | null>(null);
  const offset = filtros.offset ?? 0;

  const lista = useQuery({
    ...getListarFalhasQueryOptions({
      busca: filtros.busca,
      id_familia: filtros.id_familia,
      tipo: filtros.tipo,
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

  const desativar = async (falha: FalhaOut) => {
    try {
      await alterar.mutateAsync({ idFalha: falha.id_falha, data: { ativo: false } });
      void queryClient.invalidateQueries({ queryKey: getListarFalhasQueryKey() });
      toast.success("Registro desativado.");
    } catch (erro) {
      toast.error(mensagemDeErro(erro));
    }
  };

  const colunas = [
    coluna.accessor("codigo", {
      header: "Código",
      cell: ({ row }) => (
        <div className="flex min-w-32 items-center gap-2">
          <span className="font-mono text-sm">{row.original.codigo}</span>
          <Badge variant={row.original.tipo === "FALHA" ? "destructive" : "outline"}>
            {ROTULO_TIPO_FALHA[row.original.tipo]}
          </Badge>
        </div>
      ),
    }),
    coluna.accessor("titulo", {
      header: "Título",
      cell: ({ row }) => (
        <div className="min-w-48">
          <p className="font-medium">{row.original.titulo}</p>
          {row.original.reacao && (
            <p className="text-xs text-muted-foreground">Reação: {row.original.reacao}</p>
          )}
        </div>
      ),
    }),
    coluna.accessor("id_familia", {
      header: "Família",
      cell: ({ getValue }) => nomeFamilia(getValue()),
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
        titulo="Falhas e alarmes"
        descricao="Códigos de falha e alarme por família, com causa e solução para o técnico."
        acoes={
          podeEscrever && (
            <Button
              onClick={() => {
                setEditando(null);
                setFormAberto(true);
              }}
            >
              <Plus /> Nova falha
            </Button>
          )
        }
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
        <div className="grid gap-1.5 lg:col-span-2">
          <Label htmlFor="busca-falhas">Código ou título</Label>
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
              id="busca-falhas"
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
          <Label htmlFor="filtro-familia-fal">Família</Label>
          <ComboboxFamilia
            id="filtro-familia-fal"
            valor={filtros.id_familia}
            aoMudar={(id_familia) => {
              filtrar({ id_familia });
            }}
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="filtro-tipo-fal">Tipo</Label>
          <SelectOpcoes
            id="filtro-tipo-fal"
            valor={filtros.tipo}
            aoMudar={(tipo) => {
              filtrar({ tipo });
            }}
            opcoes={TIPOS_FALHA}
            rotulos={ROTULO_TIPO_FALHA}
            rotuloTodos="Todos"
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="filtro-idioma-fal">Idioma</Label>
          <SelectOpcoes
            id="filtro-idioma-fal"
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
          <Label htmlFor="filtro-ativo-fal">Situação</Label>
          <SelectOpcoes
            id="filtro-ativo-fal"
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
          idLinha={(f) => f.id_falha}
          mensagemVazia="Nenhuma falha com esses filtros."
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

      <FormFalha
        aberto={formAberto}
        aoMudar={setFormAberto}
        falha={editando}
        aoSalvar={() => {
          void lista.refetch();
        }}
      />

      <ConfirmarExclusao
        aberto={excluindo !== null}
        aoMudar={(aberto) => {
          if (!aberto) setExcluindo(null);
        }}
        titulo="Excluir falha?"
        descricao={
          <>
            O código <strong>{excluindo?.codigo}</strong> será removido das respostas do assistente.
          </>
        }
        aoConfirmar={async () => {
          if (!excluindo) return;
          try {
            await excluir.mutateAsync({ idFalha: excluindo.id_falha });
            queryClient.removeQueries({ queryKey: getObterFalhaQueryKey(excluindo.id_falha) });
            void queryClient.invalidateQueries({ queryKey: getListarFalhasQueryKey() });
            toast.success("Registro excluído.");
            setExcluindo(null);
          } catch (erro) {
            if (ehProblema(erro, 409)) {
              const alvo = excluindo;
              setExcluindo(null);
              toast.error("Registro com vínculos não pode ser excluído.", {
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
