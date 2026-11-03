import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { createColumnHelper } from "@tanstack/react-table";
import { Pencil, Plus, Search } from "lucide-react";
import { useState } from "react";
import { z } from "zod";

import { getListarUsuariosQueryOptions } from "@/api/gerado/auth/auth";
import { Perfil, type UsuarioOut } from "@/api/gerado/modelos";
import { BadgeAtivo } from "@/components/badge-ativo";
import { CabecalhoPagina } from "@/components/cabecalho-pagina";
import { ProblemaAlerta } from "@/components/problema-alerta";
import { SelectOpcoes } from "@/components/select-opcoes";
import { TabelaDados } from "@/components/tabela-dados";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ehAdmin, obterSessao } from "@/features/auth/sessao";
import { FormUsuario } from "@/features/usuarios/form-usuario";
import { formatarDataHora } from "@/lib/formato";
import {
  ativoDaUrl,
  esquemaFiltroAtivo,
  FILTRO_ATIVO,
  PERFIS,
  ROTULO_FILTRO_ATIVO,
  ROTULO_PERFIL,
  type FiltroAtivo,
} from "@/lib/rotulos";

const LIMITE = 20;

const esquemaFiltros = z.object({
  busca: z.string().trim().max(100).optional().catch(undefined),
  perfil: z.enum(Perfil).optional().catch(undefined),
  ativo: esquemaFiltroAtivo,
  offset: z.number().int().min(0).optional().catch(undefined),
});

export const Route = createFileRoute("/_app/usuarios")({
  beforeLoad: () => {
    if (!ehAdmin(obterSessao()?.usuario.perfil)) throw redirect({ to: "/assistente" });
  },
  validateSearch: esquemaFiltros,
  component: PaginaUsuarios,
});

const coluna = createColumnHelper<UsuarioOut>();

function PaginaUsuarios() {
  const filtros = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  const queryClient = useQueryClient();
  const [formAberto, setFormAberto] = useState(false);
  const [editando, setEditando] = useState<UsuarioOut | null>(null);
  const offset = filtros.offset ?? 0;

  const lista = useQuery({
    ...getListarUsuariosQueryOptions({
      busca: filtros.busca,
      perfil: filtros.perfil,
      ativo: ativoDaUrl(filtros.ativo),
      offset,
      limit: LIMITE,
    }),
    placeholderData: (anterior) => anterior,
  });

  const filtrar = (parcial: Partial<z.infer<typeof esquemaFiltros>>) => {
    void navigate({ search: (atual) => ({ ...atual, ...parcial, offset: undefined }), replace: true });
  };

  const colunas = [
    coluna.accessor("nome", {
      header: "Nome",
      cell: ({ row }) => (
        <div className="min-w-40">
          <p className="font-medium">{row.original.nome}</p>
          <p className="text-xs text-muted-foreground">{row.original.email}</p>
        </div>
      ),
    }),
    coluna.accessor("perfil", { header: "Perfil", cell: ({ getValue }) => ROTULO_PERFIL[getValue()] }),
    coluna.accessor("ativo", {
      header: "Situação",
      cell: ({ getValue }) => <BadgeAtivo ativo={getValue()} />,
    }),
    coluna.accessor("updated_at", {
      header: "Atualizado",
      cell: ({ getValue }) => <span className="whitespace-nowrap">{formatarDataHora(getValue())}</span>,
    }),
    coluna.display({
      id: "acoes",
      header: "",
      cell: ({ row }) => (
        <div className="flex justify-end">
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
        </div>
      ),
    }),
  ];

  return (
    <div className="space-y-4">
      <CabecalhoPagina
        titulo="Usuários"
        descricao="Perfis de acesso: ADMIN administra tudo, OPERADOR escreve no catálogo e LEITURA só consulta."
        acoes={
          <Button
            onClick={() => {
              setEditando(null);
              setFormAberto(true);
            }}
          >
            <Plus /> Novo usuário
          </Button>
        }
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="grid gap-1.5 lg:col-span-2">
          <Label htmlFor="busca-usuarios">Nome ou e-mail</Label>
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
              id="busca-usuarios"
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
          <Label htmlFor="filtro-perfil">Perfil</Label>
          <SelectOpcoes
            id="filtro-perfil"
            valor={filtros.perfil}
            aoMudar={(perfil) => {
              filtrar({ perfil });
            }}
            opcoes={PERFIS}
            rotulos={ROTULO_PERFIL}
            rotuloTodos="Todos"
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="filtro-ativo-usu">Situação</Label>
          <SelectOpcoes
            id="filtro-ativo-usu"
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
          idLinha={(u) => u.id_usuario}
          mensagemVazia="Nenhum usuário com esses filtros."
          aoMudarOffset={(novo) => {
            void navigate({ search: (atual) => ({ ...atual, offset: novo || undefined }) });
          }}
          aoClicarLinha={(u) => {
            setEditando(u);
            setFormAberto(true);
          }}
        />
      )}

      <FormUsuario
        aberto={formAberto}
        aoMudar={setFormAberto}
        usuario={editando}
        aoSalvar={() => {
          void queryClient.invalidateQueries({ queryKey: getListarUsuariosQueryOptions().queryKey });
          void lista.refetch();
        }}
      />
    </div>
  );
}
