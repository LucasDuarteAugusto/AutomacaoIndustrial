import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import {
  getListarFamiliasQueryKey,
  getObterFamiliaQueryKey,
  useAlterarFamilia,
  useCriarFamilia,
} from "@/api/gerado/familias/familias";
import type { FamiliaOut } from "@/api/gerado/modelos";
import { CriarFamiliaBody, criarFamiliaBodyNomeMax } from "@/api/gerado/zod/familias/familias";
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
import { Textarea } from "@/components/ui/textarea";
import { ComboboxFabricante, ComboboxTipoEquipamento } from "@/features/catalogo/comboboxes";

const esquema = z.object({
  id_fabricante: z.string().min(1, "Selecione o fabricante"),
  id_tipo_equipamento: z.string().min(1, "Selecione o tipo"),
  nome: CriarFamiliaBody.shape.nome.trim(),
  descricao: z.string().trim(),
  ativo: z.boolean(),
});
type Dados = z.infer<typeof esquema>;

const VAZIO: Dados = { id_fabricante: "", id_tipo_equipamento: "", nome: "", descricao: "", ativo: true };

const CAMPOS = ["id_fabricante", "id_tipo_equipamento", "nome", "descricao", "ativo"] as const;

export function FormFamilia({
  aberto,
  aoMudar,
  familia,
  aoSalvar,
}: {
  aberto: boolean;
  aoMudar: (aberto: boolean) => void;
  familia: FamiliaOut | null;
  aoSalvar: () => void;
}) {
  const queryClient = useQueryClient();
  const criar = useCriarFamilia();
  const alterar = useAlterarFamilia();
  const editando = familia !== null;

  const form = useForm<Dados>({
    resolver: zodResolver(esquema),
    defaultValues: VAZIO,
  });
  const { errors, isSubmitting } = form.formState;

  useEffect(() => {
    if (!aberto) return;
    form.reset(
      familia
        ? {
            id_fabricante: familia.id_fabricante,
            id_tipo_equipamento: familia.id_tipo_equipamento,
            nome: familia.nome,
            descricao: familia.descricao ?? "",
            ativo: familia.ativo,
          }
        : VAZIO,
    );
  }, [aberto, familia, form]);

  const enviar = form.handleSubmit(async (dados) => {
    const corpo = {
      id_fabricante: dados.id_fabricante,
      id_tipo_equipamento: dados.id_tipo_equipamento,
      nome: dados.nome,
      descricao: dados.descricao || null,
      ativo: dados.ativo,
    };
    try {
      const salvo = editando
        ? await alterar.mutateAsync({ idFamilia: familia.id_familia, data: corpo })
        : await criar.mutateAsync({ data: corpo });
      queryClient.setQueryData(getObterFamiliaQueryKey(salvo.id_familia), salvo);
      void queryClient.invalidateQueries({ queryKey: getListarFamiliasQueryKey() });
      toast.success(editando ? "Família atualizada." : "Família cadastrada.");
      aoSalvar();
      aoMudar(false);
    } catch (erro) {
      if (ehProblema(erro, 409)) {
        form.setError("nome", { type: "servidor", message: "Já existe uma família com esse nome." });
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
          <SheetTitle>{editando ? "Editar família" : "Nova família"}</SheetTitle>
          <SheetDescription>
            {editando
              ? "Altere os dados da família."
              : `Nome com até ${criarFamiliaBodyNomeMax} caracteres, único dentro do fabricante.`}
          </SheetDescription>
        </SheetHeader>
        <form onSubmit={enviar} className="flex min-h-0 flex-1 flex-col" noValidate>
          <div className="grid flex-1 gap-4 overflow-y-auto p-4">
            <AlertaFormulario mensagem={errors.root?.message} />
            <Campo id="fam-fabricante" rotulo="Fabricante" erro={errors.id_fabricante?.message}>
              <Controller
                control={form.control}
                name="id_fabricante"
                render={({ field }) => (
                  <ComboboxFabricante
                    valor={field.value || undefined}
                    aoMudar={(valor) => {
                      field.onChange(valor ?? "");
                    }}
                  />
                )}
              />
            </Campo>
            <Campo id="fam-tipo" rotulo="Tipo de equipamento" erro={errors.id_tipo_equipamento?.message}>
              <Controller
                control={form.control}
                name="id_tipo_equipamento"
                render={({ field }) => (
                  <ComboboxTipoEquipamento
                    valor={field.value || undefined}
                    aoMudar={(valor) => {
                      field.onChange(valor ?? "");
                    }}
                  />
                )}
              />
            </Campo>
            <Campo id="fam-nome" rotulo="Nome" erro={errors.nome?.message}>
              <Input placeholder="SINAMICS G120" {...form.register("nome")} />
            </Campo>
            <Campo id="fam-descricao" rotulo="Descrição" erro={errors.descricao?.message}>
              <Textarea rows={3} placeholder="Opcional" {...form.register("descricao")} />
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
