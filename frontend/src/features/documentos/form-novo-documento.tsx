import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { Controller, useForm, useWatch } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { useCriarDocumento } from "@/api/gerado/documentos/documentos";
import type { DocumentoOut } from "@/api/gerado/modelos";
import {
  CriarDocumentoBody,
  criarDocumentoBodyCodigoDocumentoOneMax,
  criarDocumentoBodyEdicaoOneMax,
  criarDocumentoBodyVersaoFirmwareOneMax,
} from "@/api/gerado/zod/documentos/documentos";
import { ehProblema, mensagemDeErro } from "@/api/problema";
import { AlertaFormulario } from "@/components/alerta-formulario";
import { Campo } from "@/components/campo";
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
import { SelecaoEquipamentos, SelecaoFamilias } from "@/features/catalogo/comboboxes";
import { IDIOMAS, ROTULO_IDIOMA, ROTULO_TIPO_DOCUMENTO, TIPOS_DOCUMENTO } from "@/lib/rotulos";

import { documentoAtualizado } from "./cache";

const opcao = z.object({
  id: z.string(),
  rotulo: z.string(),
  detalhe: z.string().optional(),
  meta: z.string().optional(),
});

const esquema = z.object({
  titulo: CriarDocumentoBody.shape.titulo.trim(),
  tipo_documento: CriarDocumentoBody.shape.tipo_documento,
  idioma: CriarDocumentoBody.shape.idioma,
  codigo_documento: z.string().trim().max(criarDocumentoBodyCodigoDocumentoOneMax),
  edicao: z.string().trim().max(criarDocumentoBodyEdicaoOneMax),
  versao_firmware: z.string().trim().max(criarDocumentoBodyVersaoFirmwareOneMax),
  familias: z.array(opcao).min(1, "Escolha pelo menos uma família."),
  equipamentos: z.array(opcao),
});
type DadosDocumento = z.infer<typeof esquema>;
type Entrada = z.input<typeof esquema>;

const VAZIO: Partial<Entrada> = {
  titulo: "",
  idioma: "pt-BR",
  codigo_documento: "",
  edicao: "",
  versao_firmware: "",
  familias: [],
  equipamentos: [],
};

const CAMPO_DA_API: Record<string, keyof DadosDocumento> = {
  titulo: "titulo",
  tipo_documento: "tipo_documento",
  idioma: "idioma",
  codigo_documento: "codigo_documento",
  edicao: "edicao",
  versao_firmware: "versao_firmware",
  ids_familias: "familias",
  ids_equipamentos: "equipamentos",
};

export function FormNovoDocumento({
  aberto,
  aoMudar,
  aoCriar,
}: {
  aberto: boolean;
  aoMudar: (aberto: boolean) => void;
  aoCriar: (documento: DocumentoOut) => void;
}) {
  const queryClient = useQueryClient();
  const criar = useCriarDocumento();
  const form = useForm<Entrada, unknown, DadosDocumento>({
    resolver: zodResolver(esquema),
    defaultValues: VAZIO,
  });
  const { errors, isSubmitting } = form.formState;
  const familias = useWatch({ control: form.control, name: "familias" });

  const enviar = form.handleSubmit(async (dados) => {
    try {
      const documento = await criar.mutateAsync({
        data: {
          titulo: dados.titulo,
          tipo_documento: dados.tipo_documento,
          idioma: dados.idioma,
          codigo_documento: dados.codigo_documento || null,
          edicao: dados.edicao || null,
          versao_firmware: dados.versao_firmware || null,
          ids_familias: dados.familias.map((f) => f.id),
          ids_equipamentos: dados.equipamentos.map((e) => e.id),
        },
      });
      documentoAtualizado(queryClient, documento);
      toast.success("Documento cadastrado. Agora envie o PDF.");
      form.reset(VAZIO);
      aoCriar(documento);
    } catch (erro) {
      let aplicou = false;
      if (ehProblema(erro, 422)) {
        for (const item of erro.erros) {
          const campo = CAMPO_DA_API[String(item.loc[1])];
          if (item.loc[0] === "body" && campo) {
            form.setError(campo, { message: item.msg });
            aplicou = true;
          }
        }
      }
      if (!aplicou) form.setError("root", { message: mensagemDeErro(erro) });
    }
  });

  return (
    <Sheet
      open={aberto}
      onOpenChange={(valor) => {
        if (!isSubmitting) aoMudar(valor);
      }}
    >
      <SheetContent className="flex w-full flex-col gap-0 sm:max-w-xl">
        <SheetHeader className="border-b">
          <SheetTitle>Novo documento</SheetTitle>
          <SheetDescription>Cadastre os metadados; o PDF é enviado na página do documento.</SheetDescription>
        </SheetHeader>
        <form onSubmit={enviar} className="flex min-h-0 flex-1 flex-col" noValidate>
          <div className="grid flex-1 gap-4 overflow-y-auto p-4">
            <AlertaFormulario mensagem={errors.root?.message} />
            <Campo id="doc-titulo" rotulo="Título" erro={errors.titulo?.message}>
              <Input placeholder="SINAMICS G120 - Lista de parâmetros" {...form.register("titulo")} />
            </Campo>
            <div className="grid gap-4 sm:grid-cols-2">
              <Campo id="doc-tipo" rotulo="Tipo" erro={errors.tipo_documento?.message}>
                <Controller
                  control={form.control}
                  name="tipo_documento"
                  render={({ field }) => (
                    <SelectOpcoes
                      valor={field.value}
                      aoMudar={field.onChange}
                      opcoes={TIPOS_DOCUMENTO}
                      rotulos={ROTULO_TIPO_DOCUMENTO}
                    />
                  )}
                />
              </Campo>
              <Campo id="doc-idioma" rotulo="Idioma" erro={errors.idioma?.message}>
                <Controller
                  control={form.control}
                  name="idioma"
                  render={({ field }) => (
                    <SelectOpcoes
                      valor={field.value}
                      aoMudar={field.onChange}
                      opcoes={IDIOMAS}
                      rotulos={ROTULO_IDIOMA}
                    />
                  )}
                />
              </Campo>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <Campo id="doc-codigo" rotulo="Código no fabricante" erro={errors.codigo_documento?.message}>
                <Input placeholder="A5E33840768" {...form.register("codigo_documento")} />
              </Campo>
              <Campo id="doc-edicao" rotulo="Edição" erro={errors.edicao?.message}>
                <Input placeholder="09/2023" {...form.register("edicao")} />
              </Campo>
              <Campo id="doc-firmware" rotulo="Firmware" erro={errors.versao_firmware?.message}>
                <Input placeholder="4.7 SP14" {...form.register("versao_firmware")} />
              </Campo>
            </div>
            <Campo
              id="doc-familias"
              rotulo="Famílias cobertas"
              erro={errors.familias?.message}
              dica="Pelo menos uma. O documento aparece nas buscas filtradas por essas famílias."
            >
              <Controller
                control={form.control}
                name="familias"
                render={({ field }) => (
                  <SelecaoFamilias
                    selecionadas={field.value}
                    aoMudar={(novas) => {
                      field.onChange(novas);
                      const ids = new Set(novas.map((f) => f.id));
                      const equipamentos = form.getValues("equipamentos");
                      form.setValue(
                        "equipamentos",
                        equipamentos.filter((e) => e.meta !== undefined && ids.has(e.meta)),
                      );
                    }}
                  />
                )}
              />
            </Campo>
            <Campo
              id="doc-equipamentos"
              rotulo="Equipamentos específicos (opcional)"
              erro={errors.equipamentos?.message}
              dica="Só modelos das famílias escolhidas."
            >
              <Controller
                control={form.control}
                name="equipamentos"
                render={({ field }) => (
                  <SelecaoEquipamentos
                    idsFamilias={familias.map((f) => f.id)}
                    selecionadas={field.value}
                    aoMudar={field.onChange}
                  />
                )}
              />
            </Campo>
          </div>
          <SheetFooter className="border-t">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="animate-spin" />}
              Cadastrar documento
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
}
