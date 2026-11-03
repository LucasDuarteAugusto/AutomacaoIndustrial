import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import {
  getListarEquipamentosQueryKey,
  getObterEquipamentoQueryKey,
  useAlterarEquipamento,
  useCriarEquipamento,
} from "@/api/gerado/equipamentos/equipamentos";
import type { EquipamentoOut } from "@/api/gerado/modelos";
import {
  CriarEquipamentoBody,
  criarEquipamentoBodyTensaoNominalVOneMax,
} from "@/api/gerado/zod/equipamentos/equipamentos";
import { aplicarErrosNoFormulario, ehProblema, mensagemDeErro } from "@/api/problema";
import { AlertaFormulario } from "@/components/alerta-formulario";
import { Campo } from "@/components/campo";
import { CampoAtivo } from "@/components/campo-ativo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { ComboboxFamilia } from "@/features/catalogo/comboboxes";

/** Campo numérico opcional preenchido como texto (aceita vírgula decimal). */
const numeroDecimal = (rotulo: string) =>
  z
    .string()
    .trim()
    .refine(
      (valor) => valor === "" || (/^\d+([.,]\d+)?$/.test(valor) && Number(valor.replace(",", ".")) >= 0),
      `${rotulo}: informe um número maior ou igual a zero`,
    );

const numeroInteiro = (rotulo: string, maximo: number) =>
  z
    .string()
    .trim()
    .refine(
      (valor) => valor === "" || (/^\d+$/.test(valor) && Number(valor) <= maximo),
      `${rotulo}: informe um inteiro entre 0 e ${maximo}`,
    );

const esquema = z.object({
  id_familia: z.string().min(1, "Selecione a família"),
  codigo_pedido: CriarEquipamentoBody.shape.codigo_pedido.trim(),
  nome: CriarEquipamentoBody.shape.nome.trim(),
  potencia_kw: numeroDecimal("Potência"),
  tensao_nominal_v: numeroInteiro("Tensão", criarEquipamentoBodyTensaoNominalVOneMax),
  corrente_nominal_a: numeroDecimal("Corrente"),
  ativo: z.boolean(),
});
type Dados = z.infer<typeof esquema>;

const VAZIO: Dados = {
  id_familia: "",
  codigo_pedido: "",
  nome: "",
  potencia_kw: "",
  tensao_nominal_v: "",
  corrente_nominal_a: "",
  ativo: true,
};

const CAMPOS = [
  "id_familia",
  "codigo_pedido",
  "nome",
  "potencia_kw",
  "tensao_nominal_v",
  "corrente_nominal_a",
  "ativo",
] as const;

function paraNumero(valor: string): number | null {
  return valor === "" ? null : Number(valor.replace(",", "."));
}

function paraTexto(valor: number | null): string {
  return valor === null ? "" : String(valor);
}

export function FormEquipamento({
  aberto,
  aoMudar,
  equipamento,
  aoSalvar,
}: {
  aberto: boolean;
  aoMudar: (aberto: boolean) => void;
  equipamento: EquipamentoOut | null;
  aoSalvar: () => void;
}) {
  const queryClient = useQueryClient();
  const criar = useCriarEquipamento();
  const alterar = useAlterarEquipamento();
  const editando = equipamento !== null;

  const form = useForm<Dados>({
    resolver: zodResolver(esquema),
    defaultValues: VAZIO,
  });
  const { errors, isSubmitting } = form.formState;

  useEffect(() => {
    if (!aberto) return;
    form.reset(
      equipamento
        ? {
            id_familia: equipamento.id_familia,
            codigo_pedido: equipamento.codigo_pedido,
            nome: equipamento.nome,
            potencia_kw: paraTexto(equipamento.potencia_kw),
            tensao_nominal_v: paraTexto(equipamento.tensao_nominal_v),
            corrente_nominal_a: paraTexto(equipamento.corrente_nominal_a),
            ativo: equipamento.ativo,
          }
        : VAZIO,
    );
  }, [aberto, equipamento, form]);

  const enviar = form.handleSubmit(async (dados) => {
    const corpo = {
      id_familia: dados.id_familia,
      codigo_pedido: dados.codigo_pedido,
      nome: dados.nome,
      potencia_kw: paraNumero(dados.potencia_kw),
      tensao_nominal_v: paraNumero(dados.tensao_nominal_v),
      corrente_nominal_a: paraNumero(dados.corrente_nominal_a),
      ativo: dados.ativo,
    };
    try {
      const salvo = editando
        ? await alterar.mutateAsync({ idEquipamento: equipamento.id_equipamento, data: corpo })
        : await criar.mutateAsync({ data: corpo });
      queryClient.setQueryData(getObterEquipamentoQueryKey(salvo.id_equipamento), salvo);
      void queryClient.invalidateQueries({ queryKey: getListarEquipamentosQueryKey() });
      toast.success(editando ? "Equipamento atualizado." : "Equipamento cadastrado.");
      aoSalvar();
      aoMudar(false);
    } catch (erro) {
      if (ehProblema(erro, 409)) {
        form.setError("codigo_pedido", {
          type: "servidor",
          message: "Já existe um equipamento com esse código nesta família.",
        });
      } else if (!aplicarErrosNoFormulario(erro, form.setError, CAMPOS)) {
        form.setError("root", { message: mensagemDeErro(erro) });
      }
    }
  });

  return (
    <Sheet
      open={aberto}
      onOpenChange={(valor) => {
        if (!isSubmitting) aoMudar(valor);
      }}
    >
      <SheetContent className="flex w-full flex-col gap-0 sm:max-w-md">
        <SheetHeader className="border-b">
          <SheetTitle>{editando ? "Editar equipamento" : "Novo equipamento"}</SheetTitle>
          <SheetDescription>
            {editando ? "Altere os dados do equipamento." : "O código do pedido é único dentro da família."}
          </SheetDescription>
        </SheetHeader>
        <form onSubmit={enviar} className="flex min-h-0 flex-1 flex-col" noValidate>
          <div className="grid flex-1 gap-4 overflow-y-auto p-4">
            <AlertaFormulario mensagem={errors.root?.message} />
            <Campo id="eq-familia" rotulo="Família" erro={errors.id_familia?.message}>
              <Controller
                control={form.control}
                name="id_familia"
                render={({ field }) => (
                  <ComboboxFamilia
                    valor={field.value || undefined}
                    aoMudar={(valor) => {
                      field.onChange(valor ?? "");
                    }}
                  />
                )}
              />
            </Campo>
            <Campo id="eq-codigo" rotulo="Código do pedido" erro={errors.codigo_pedido?.message}>
              <Input placeholder="6SL3210-1KE21-3UF1" {...form.register("codigo_pedido")} />
            </Campo>
            <Campo id="eq-nome" rotulo="Nome" erro={errors.nome?.message}>
              <Input placeholder="SINAMICS G120C 3 kW" {...form.register("nome")} />
            </Campo>
            <div className="grid gap-4 sm:grid-cols-2">
              <Campo id="eq-tensao" rotulo="Tensão nominal (V)" erro={errors.tensao_nominal_v?.message}>
                <Input inputMode="numeric" placeholder="380" {...form.register("tensao_nominal_v")} />
              </Campo>
              <Campo id="eq-corrente" rotulo="Corrente nominal (A)" erro={errors.corrente_nominal_a?.message}>
                <Input inputMode="decimal" placeholder="7,3" {...form.register("corrente_nominal_a")} />
              </Campo>
            </div>
            <Campo id="eq-potencia" rotulo="Potência (kW)" erro={errors.potencia_kw?.message}>
              <Input inputMode="decimal" placeholder="3" {...form.register("potencia_kw")} />
            </Campo>
            <CampoAtivo control={form.control} erro={errors.ativo?.message} />
          </div>
          <SheetFooter className="border-t">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="animate-spin" />}
              {editando ? "Salvar" : "Cadastrar"}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
}
