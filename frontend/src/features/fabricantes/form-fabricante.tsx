import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import {
  getListarFabricantesQueryKey,
  getObterFabricanteQueryKey,
  useAlterarFabricante,
  useCriarFabricante,
} from "@/api/gerado/fabricantes/fabricantes";
import type { FabricanteOut } from "@/api/gerado/modelos";
import {
  CriarFabricanteBody,
  criarFabricanteBodyNomeMax,
  criarFabricanteBodySiteOneMax,
} from "@/api/gerado/zod/fabricantes/fabricantes";
import { aplicarErrosNoFormulario, mensagemDeErro } from "@/api/problema";
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

const esquema = z.object({
  nome: CriarFabricanteBody.shape.nome.trim(),
  site: z.string().trim().max(criarFabricanteBodySiteOneMax),
  ativo: z.boolean(),
});
type Dados = z.infer<typeof esquema>;

const VAZIO: Dados = { nome: "", site: "", ativo: true };

const CAMPOS = ["nome", "site", "ativo"] as const;

export function FormFabricante({
  aberto,
  aoMudar,
  fabricante,
  aoSalvar,
}: {
  aberto: boolean;
  aoMudar: (aberto: boolean) => void;
  fabricante: FabricanteOut | null;
  aoSalvar: () => void;
}) {
  const queryClient = useQueryClient();
  const criar = useCriarFabricante();
  const alterar = useAlterarFabricante();
  const editando = fabricante !== null;

  const form = useForm<Dados>({
    resolver: zodResolver(esquema),
    defaultValues: VAZIO,
  });
  const { errors, isSubmitting } = form.formState;

  useEffect(() => {
    if (!aberto) return;
    form.reset(
      fabricante
        ? { nome: fabricante.nome, site: fabricante.site ?? "", ativo: fabricante.ativo }
        : VAZIO,
    );
  }, [aberto, fabricante, form]);

  const enviar = form.handleSubmit(async (dados) => {
    const corpo = { nome: dados.nome, site: dados.site || null, ativo: dados.ativo };
    try {
      const salvo = editando
        ? await alterar.mutateAsync({ idFabricante: fabricante.id_fabricante, data: corpo })
        : await criar.mutateAsync({ data: corpo });
      queryClient.setQueryData(getObterFabricanteQueryKey(salvo.id_fabricante), salvo);
      void queryClient.invalidateQueries({ queryKey: getListarFabricantesQueryKey() });
      toast.success(editando ? "Fabricante atualizado." : "Fabricante cadastrado.");
      aoSalvar();
      aoMudar(false);
    } catch (erro) {
      if (!aplicarErrosNoFormulario(erro, form.setError, CAMPOS)) {
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
          <SheetTitle>{editando ? "Editar fabricante" : "Novo fabricante"}</SheetTitle>
          <SheetDescription>
            {editando
              ? "Altere os dados do fabricante."
              : `Nome com até ${criarFabricanteBodyNomeMax} caracteres.`}
          </SheetDescription>
        </SheetHeader>
        <form onSubmit={enviar} className="flex min-h-0 flex-1 flex-col" noValidate>
          <div className="grid flex-1 gap-4 overflow-y-auto p-4">
            <AlertaFormulario mensagem={errors.root?.message} />
            <Campo id="fab-nome" rotulo="Nome" erro={errors.nome?.message}>
              <Input placeholder="Siemens" {...form.register("nome")} />
            </Campo>
            <Campo id="fab-site" rotulo="Site" erro={errors.site?.message}>
              <Input placeholder="https://…" type="url" {...form.register("site")} />
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
