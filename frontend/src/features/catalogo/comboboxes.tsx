import { useQuery } from "@tanstack/react-query";

import {
  getListarEquipamentosQueryOptions,
  getObterEquipamentoQueryOptions,
  listarEquipamentos,
} from "@/api/gerado/equipamentos/equipamentos";
import {
  getListarFabricantesQueryOptions,
  getObterFabricanteQueryOptions,
} from "@/api/gerado/fabricantes/fabricantes";
import { getListarFamiliasQueryOptions, getObterFamiliaQueryOptions } from "@/api/gerado/familias/familias";
import type { EquipamentoOut, PaginaEquipamentoOut, PaginaFamiliaOut } from "@/api/gerado/modelos";
import { ComboboxAssincrono, type Opcao } from "@/components/combobox-assincrono";
import { SelecaoMultipla } from "@/components/selecao-multipla";

const LIMITE_OPCOES = 20;

interface PropsCombobox {
  id?: string;
  valor: string | undefined;
  aoMudar: (id: string | undefined) => void;
  desabilitado?: boolean;
}

function opcaoEquipamento(e: EquipamentoOut): Opcao {
  return { id: e.id_equipamento, rotulo: e.codigo_pedido, detalhe: e.nome, meta: e.id_familia };
}

function opcoesFamilias(pagina: PaginaFamiliaOut): Opcao[] {
  return pagina.items.map((f) => ({ id: f.id_familia, rotulo: f.nome }));
}

export function ComboboxFabricante({ id, valor, aoMudar, desabilitado }: PropsCombobox) {
  const selecionado = useQuery({ ...getObterFabricanteQueryOptions(valor ?? ""), enabled: !!valor });
  return (
    <ComboboxAssincrono
      id={id}
      valor={valor}
      aoMudar={(opcao) => {
        aoMudar(opcao?.id);
      }}
      consulta={(busca) =>
        getListarFabricantesQueryOptions({ busca: busca || undefined, ativo: true, limit: LIMITE_OPCOES })
      }
      mapear={(pagina) => pagina.items.map((f) => ({ id: f.id_fabricante, rotulo: f.nome }))}
      rotuloSelecionado={selecionado.data?.nome}
      placeholder="Todos os fabricantes"
      desabilitado={desabilitado}
    />
  );
}

export function ComboboxFamilia({
  id,
  valor,
  aoMudar,
  desabilitado,
  idFabricante,
}: PropsCombobox & { idFabricante?: string | undefined }) {
  const selecionado = useQuery({ ...getObterFamiliaQueryOptions(valor ?? ""), enabled: !!valor });
  return (
    <ComboboxAssincrono
      id={id}
      valor={valor}
      aoMudar={(opcao) => {
        aoMudar(opcao?.id);
      }}
      consulta={(busca) =>
        getListarFamiliasQueryOptions({
          busca: busca || undefined,
          id_fabricante: idFabricante,
          ativo: true,
          limit: LIMITE_OPCOES,
        })
      }
      mapear={opcoesFamilias}
      rotuloSelecionado={selecionado.data?.nome}
      placeholder="Todas as famílias"
      desabilitado={desabilitado}
    />
  );
}

export function ComboboxEquipamento({
  id,
  valor,
  aoMudar,
  desabilitado,
  idFamilia,
}: PropsCombobox & { idFamilia?: string | undefined }) {
  const selecionado = useQuery({ ...getObterEquipamentoQueryOptions(valor ?? ""), enabled: !!valor });
  return (
    <ComboboxAssincrono
      id={id}
      valor={valor}
      aoMudar={(opcao) => {
        aoMudar(opcao?.id);
      }}
      consulta={(busca) =>
        getListarEquipamentosQueryOptions({
          busca: busca || undefined,
          id_familia: idFamilia,
          ativo: true,
          limit: LIMITE_OPCOES,
        })
      }
      mapear={(pagina) => pagina.items.map(opcaoEquipamento)}
      rotuloSelecionado={selecionado.data?.codigo_pedido}
      placeholder="Todos os equipamentos"
      desabilitado={desabilitado}
    />
  );
}

interface PropsSelecao {
  id?: string;
  selecionadas: Opcao[];
  aoMudar: (opcoes: Opcao[]) => void;
  desabilitado?: boolean;
  "aria-invalid"?: boolean;
  "aria-describedby"?: string;
}

export function SelecaoFamilias(props: PropsSelecao) {
  return (
    <SelecaoMultipla
      {...props}
      placeholder="Adicionar família…"
      consulta={(busca) =>
        getListarFamiliasQueryOptions({ busca: busca || undefined, ativo: true, limit: LIMITE_OPCOES })
      }
      mapear={opcoesFamilias}
    />
  );
}

/** Equipamentos das famílias escolhidas (a API filtra uma família por vez; as consultas rodam em paralelo). */
export function SelecaoEquipamentos({ idsFamilias, ...props }: PropsSelecao & { idsFamilias: string[] }) {
  return (
    <SelecaoMultipla<EquipamentoOut[]>
      {...props}
      desabilitado={(props.desabilitado ?? false) || idsFamilias.length === 0}
      placeholder={idsFamilias.length === 0 ? "Escolha uma família primeiro" : "Adicionar equipamento…"}
      consulta={(busca) => ({
        queryKey: ["equipamentos-das-familias", idsFamilias, busca],
        queryFn: async ({ signal }) => {
          const paginas: PaginaEquipamentoOut[] = await Promise.all(
            idsFamilias.map((idFamilia) =>
              listarEquipamentos(
                { id_familia: idFamilia, busca: busca || undefined, ativo: true, limit: LIMITE_OPCOES },
                { signal },
              ),
            ),
          );
          return paginas.flatMap((p) => p.items);
        },
      })}
      mapear={(equipamentos) => equipamentos.map(opcaoEquipamento)}
    />
  );
}
