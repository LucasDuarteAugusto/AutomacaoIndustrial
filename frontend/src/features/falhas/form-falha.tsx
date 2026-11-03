import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import {
  getListarFalhasQueryKey,
  getObterFalhaQueryKey,
  useAlterarFalha,
  useCriarFalha,
} from "@/api/gerado/falhas/falhas";
import { Idioma, TipoFalha, type FalhaOut } from "@/api/gerado/modelos";
import {
  CriarFalhaBody,
  criarFalhaBodyReacaoOneMax,
  criarFalhaBodyVersaoFirmwareOneMax,
} from "@/api/gerado/zod/falhas/falhas";
import { aplicarErrosNoFormulario, ehProblema, mensagemDeErro } from "@/api/problema";
import { AlertaFormulario } from "@/components/alerta-formulario";
import { Campo } from "@/components/campo";
import { CampoAtivo } from "@/components/campo-ativo";
import { SelectOpcoes } from "@/components/select-opcoes";
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
import { ComboboxDocumento, ComboboxFamilia } from "@/features/catalogo/comboboxes";
import { IDIOMAS, ROTULO_IDIOMA, ROTULO_TIPO_FALHA, TIPOS_FALHA } from "@/lib/rotulos";

const paginaSchema = z
  .string()
  .trim()
  .refine(
    (valor) => valor === "" || (/^\d+$/.test(valor) && Number(valor) >= 1),
    "Página: informe um inteiro maior ou igual a 1",
  );

const esquema = z.object({
  id_familia: z.string().min(1, "Selecione a família"),
  codigo: CriarFalhaBody.shape.codigo.trim(),
  tipo: z.enum(TipoFalha),
  titulo: CriarFalhaBody.shape.titulo.trim(),
  idioma: z.enum(Idioma),
  versao_firmware: z.string().trim().max(criarFalhaBodyVersaoFirmwareOneMax),
  descricao: z.string().trim(),
  causa: z.string().trim(),
  solucao: z.string().trim(),
  reacao: z.string().trim().max(criarFalhaBodyReacaoOneMax),
  id_documento: z.string(),
  pagina: paginaSchema,
  ativo: z.boolean(),
});
type Dados = z.infer<typeof esquema>;

const VAZIO: Dados = {
  id_familia: "",
  codigo: "",
  tipo: "FALHA",
  titulo: "",
  idioma: "pt-BR",
  versao_firmware: "",
  descricao: "",
  causa: "",
  solucao: "",
  reacao: "",
  id_documento: "",
  pagina: "",
  ativo: true,
};

const CAMPOS = [
  "id_familia",
  "codigo",
  "tipo",
  "titulo",
  "idioma",
  "versao_firmware",
  "descricao",
  "causa",
  "solucao",
  "reacao",
  "id_documento",
  "pagina",
  "ativo",
] as const;

export function FormFalha({
  aberto,
  aoMudar,
  falha,
  aoSalvar,
}: {
  aberto: boolean;
  aoMudar: (aberto: boolean) => void;
  falha: FalhaOut | null;
  aoSalvar: () => void;
}) {
  const queryClient = useQueryClient();
  const criar = useCriarFalha();
  const alterar = useAlterarFalha();
  const editando = falha !== null;

  const form = useForm<Dados>({
    resolver: zodResolver(esquema),
    defaultValues: VAZIO,
  });
  const { errors, isSubmitting } = form.formState;

  useEffect(() => {
    if (!aberto) return;
    form.reset(
      falha
        ? {
            id_familia: falha.id_familia,
            codigo: falha.codigo,
            tipo: falha.tipo,
            titulo: falha.titulo,
            idioma: falha.idioma,
            versao_firmware: falha.versao_firmware ?? "",
            descricao: falha.descricao ?? "",
            causa: falha.causa ?? "",
            solucao: falha.solucao ?? "",
            reacao: falha.reacao ?? "",
            id_documento: falha.id_documento ?? "",
            pagina: falha.pagina === null ? "" : String(falha.pagina),
            ativo: falha.ativo,
          }
        : VAZIO,
    );
  }, [aberto, falha, form]);

  const enviar = form.handleSubmit(async (dados) => {
    const corpo = {
      id_familia: dados.id_familia,
      codigo: dados.codigo,
      tipo: dados.tipo,
      titulo: dados.titulo,
      idioma: dados.idioma,
      versao_firmware: dados.versao_firmware || null,
      descricao: dados.descricao || null,
      causa: dados.causa || null,
      solucao: dados.solucao || null,
      reacao: dados.reacao || null,
      id_documento: dados.id_documento || null,
      pagina: dados.pagina === "" ? null : Number(dados.pagina),
      ativo: dados.ativo,
    };
    try {
      const salvo = editando
        ? await alterar.mutateAsync({ idFalha: falha.id_falha, data: corpo })
        : await criar.mutateAsync({ data: corpo });
      queryClient.setQueryData(getObterFalhaQueryKey(salvo.id_falha), salvo);
      void queryClient.invalidateQueries({ queryKey: getListarFalhasQueryKey() });
      toast.success(editando ? "Falha atualizada." : "Falha cadastrada.");
      aoSalvar();
      aoMudar(false);
    } catch (erro) {
      if (ehProblema(erro, 409)) {
        form.setError("codigo", {
          type: "servidor",
          message: "Já existe uma falha com esse código nesta família.",
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
      <SheetContent className="flex w-full flex-col gap-0 sm:max-w-lg">
        <SheetHeader className="border-b">
          <SheetTitle>{editando ? "Editar falha" : "Nova falha"}</SheetTitle>
          <SheetDescription>
            {editando
              ? "Altere os dados da falha."
              : "Código único dentro da família (e versão de firmware)."}
          </SheetDescription>
        </SheetHeader>
        <form onSubmit={enviar} className="flex min-h-0 flex-1 flex-col" noValidate>
          <div className="grid flex-1 gap-4 overflow-y-auto p-4">
            <AlertaFormulario mensagem={errors.root?.message} />
            <Campo id="fal-familia" rotulo="Família" erro={errors.id_familia?.message}>
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
            <div className="grid gap-4 sm:grid-cols-3">
              <Campo id="fal-codigo" rotulo="Código" erro={errors.codigo?.message}>
                <Input placeholder="F0001" {...form.register("codigo")} />
              </Campo>
              <Campo id="fal-tipo" rotulo="Tipo" erro={errors.tipo?.message}>
                <Controller
                  control={form.control}
                  name="tipo"
                  render={({ field }) => (
                    <SelectOpcoes
                      valor={field.value}
                      aoMudar={(valor) => {
                        if (valor) field.onChange(valor);
                      }}
                      opcoes={TIPOS_FALHA}
                      rotulos={ROTULO_TIPO_FALHA}
                    />
                  )}
                />
              </Campo>
              <Campo id="fal-idioma" rotulo="Idioma" erro={errors.idioma?.message}>
                <Controller
                  control={form.control}
                  name="idioma"
                  render={({ field }) => (
                    <SelectOpcoes
                      valor={field.value}
                      aoMudar={(valor) => {
                        if (valor) field.onChange(valor);
                      }}
                      opcoes={IDIOMAS}
                      rotulos={ROTULO_IDIOMA}
                    />
                  )}
                />
              </Campo>
            </div>
            <Campo id="fal-titulo" rotulo="Título" erro={errors.titulo?.message}>
              <Input placeholder="Sobrecorrente no motor" {...form.register("titulo")} />
            </Campo>
            <Campo id="fal-descricao" rotulo="Descrição" erro={errors.descricao?.message}>
              <Textarea rows={2} placeholder="Opcional" {...form.register("descricao")} />
            </Campo>
            <Campo id="fal-causa" rotulo="Causa" erro={errors.causa?.message}>
              <Textarea rows={2} placeholder="Opcional" {...form.register("causa")} />
            </Campo>
            <Campo id="fal-solucao" rotulo="Solução" erro={errors.solucao?.message}>
              <Textarea rows={2} placeholder="Opcional" {...form.register("solucao")} />
            </Campo>
            <div className="grid gap-4 sm:grid-cols-2">
              <Campo id="fal-reacao" rotulo="Reação" erro={errors.reacao?.message}>
                <Input placeholder="Desliga o motor" {...form.register("reacao")} />
              </Campo>
              <Campo id="fal-firmware" rotulo="Versão de firmware" erro={errors.versao_firmware?.message}>
                <Input placeholder="4.7 SP14" {...form.register("versao_firmware")} />
              </Campo>
            </div>
            <Campo id="fal-documento" rotulo="Documento de origem" erro={errors.id_documento?.message}>
              <Controller
                control={form.control}
                name="id_documento"
                render={({ field }) => (
                  <ComboboxDocumento
                    valor={field.value || undefined}
                    aoMudar={(valor) => {
                      field.onChange(valor ?? "");
                    }}
                  />
                )}
              />
            </Campo>
            <Campo id="fal-pagina" rotulo="Página no documento" erro={errors.pagina?.message}>
              <Input inputMode="numeric" placeholder="212" {...form.register("pagina")} />
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
