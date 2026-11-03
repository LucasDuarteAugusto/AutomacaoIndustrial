import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Idioma, type ParametroOut } from "@/api/gerado/modelos";
import {
  getListarParametrosQueryKey,
  getObterParametroQueryKey,
  useAlterarParametro,
  useCriarParametro,
} from "@/api/gerado/parametros/parametros";
import {
  CriarParametroBody,
  criarParametroBodyGrupoOneMax,
  criarParametroBodyNomeOneMax,
  criarParametroBodyUnidadeOneMax,
  criarParametroBodyValorPadraoOneMax,
  criarParametroBodyVersaoFirmwareOneMax,
} from "@/api/gerado/zod/parametros/parametros";
import { aplicarErrosNoFormulario, ehProblema, mensagemDeErro } from "@/api/problema";
import { AlertaFormulario } from "@/components/alerta-formulario";
import { Campo } from "@/components/campo";
import { CampoAtivo } from "@/components/campo-ativo";
import { SelectOpcoes } from "@/components/select-opcoes";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import { IDIOMAS, ROTULO_IDIOMA } from "@/lib/rotulos";

/** Campo numérico opcional preenchido como texto (aceita vírgula decimal). */
const numeroDecimal = (rotulo: string) =>
  z
    .string()
    .trim()
    .refine((valor) => valor === "" || /^-?\d+([.,]\d+)?$/.test(valor), `${rotulo}: informe um número`);

const paginaSchema = z
  .string()
  .trim()
  .refine(
    (valor) => valor === "" || (/^\d+$/.test(valor) && Number(valor) >= 1),
    "Página: informe um inteiro maior ou igual a 1",
  );

const esquema = z.object({
  id_familia: z.string().min(1, "Selecione a família"),
  codigo: CriarParametroBody.shape.codigo.trim(),
  descricao: CriarParametroBody.shape.descricao.trim(),
  nome: z.string().trim().max(criarParametroBodyNomeOneMax),
  unidade: z.string().trim().max(criarParametroBodyUnidadeOneMax),
  grupo: z.string().trim().max(criarParametroBodyGrupoOneMax),
  versao_firmware: z.string().trim().max(criarParametroBodyVersaoFirmwareOneMax),
  idioma: z.enum(Idioma),
  valor_min: numeroDecimal("Valor mínimo"),
  valor_max: numeroDecimal("Valor máximo"),
  valor_padrao: z.string().trim().max(criarParametroBodyValorPadraoOneMax),
  somente_leitura: z.boolean(),
  id_documento: z.string(),
  pagina: paginaSchema,
  ativo: z.boolean(),
});
type Dados = z.infer<typeof esquema>;

const VAZIO: Dados = {
  id_familia: "",
  codigo: "",
  descricao: "",
  nome: "",
  unidade: "",
  grupo: "",
  versao_firmware: "",
  idioma: "pt-BR",
  valor_min: "",
  valor_max: "",
  valor_padrao: "",
  somente_leitura: false,
  id_documento: "",
  pagina: "",
  ativo: true,
};

const CAMPOS = [
  "id_familia",
  "codigo",
  "descricao",
  "nome",
  "unidade",
  "grupo",
  "versao_firmware",
  "idioma",
  "valor_min",
  "valor_max",
  "valor_padrao",
  "somente_leitura",
  "id_documento",
  "pagina",
  "ativo",
] as const;

function paraNumero(valor: string): number | null {
  return valor === "" ? null : Number(valor.replace(",", "."));
}

function paraTexto(valor: number | null): string {
  return valor === null ? "" : String(valor);
}

export function FormParametro({
  aberto,
  aoMudar,
  parametro,
  aoSalvar,
}: {
  aberto: boolean;
  aoMudar: (aberto: boolean) => void;
  parametro: ParametroOut | null;
  aoSalvar: () => void;
}) {
  const queryClient = useQueryClient();
  const criar = useCriarParametro();
  const alterar = useAlterarParametro();
  const editando = parametro !== null;

  const form = useForm<Dados>({
    resolver: zodResolver(esquema),
    defaultValues: VAZIO,
  });
  const { errors, isSubmitting } = form.formState;

  useEffect(() => {
    if (!aberto) return;
    form.reset(
      parametro
        ? {
            id_familia: parametro.id_familia,
            codigo: parametro.codigo,
            descricao: parametro.descricao,
            nome: parametro.nome ?? "",
            unidade: parametro.unidade ?? "",
            grupo: parametro.grupo ?? "",
            versao_firmware: parametro.versao_firmware ?? "",
            idioma: parametro.idioma,
            valor_min: paraTexto(parametro.valor_min),
            valor_max: paraTexto(parametro.valor_max),
            valor_padrao: parametro.valor_padrao ?? "",
            somente_leitura: parametro.somente_leitura,
            id_documento: parametro.id_documento ?? "",
            pagina: paraTexto(parametro.pagina),
            ativo: parametro.ativo,
          }
        : VAZIO,
    );
  }, [aberto, parametro, form]);

  const enviar = form.handleSubmit(async (dados) => {
    const corpo = {
      id_familia: dados.id_familia,
      codigo: dados.codigo,
      descricao: dados.descricao,
      idioma: dados.idioma,
      versao_firmware: dados.versao_firmware || null,
      nome: dados.nome || null,
      unidade: dados.unidade || null,
      valor_min: paraNumero(dados.valor_min),
      valor_max: paraNumero(dados.valor_max),
      valor_padrao: dados.valor_padrao || null,
      grupo: dados.grupo || null,
      somente_leitura: dados.somente_leitura,
      id_documento: dados.id_documento || null,
      pagina: dados.pagina === "" ? null : Number(dados.pagina),
      ativo: dados.ativo,
    };
    try {
      const salvo = editando
        ? await alterar.mutateAsync({ idParametro: parametro.id_parametro, data: corpo })
        : await criar.mutateAsync({ data: corpo });
      queryClient.setQueryData(getObterParametroQueryKey(salvo.id_parametro), salvo);
      void queryClient.invalidateQueries({ queryKey: getListarParametrosQueryKey() });
      toast.success(editando ? "Parâmetro atualizado." : "Parâmetro cadastrado.");
      aoSalvar();
      aoMudar(false);
    } catch (erro) {
      if (ehProblema(erro, 409)) {
        form.setError("codigo", {
          type: "servidor",
          message: "Já existe um parâmetro com esse código nesta família.",
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
          <SheetTitle>{editando ? "Editar parâmetro" : "Novo parâmetro"}</SheetTitle>
          <SheetDescription>
            {editando
              ? "Altere os dados do parâmetro."
              : "Código único dentro da família (e versão de firmware)."}
          </SheetDescription>
        </SheetHeader>
        <form onSubmit={enviar} className="flex min-h-0 flex-1 flex-col" noValidate>
          <div className="grid flex-1 gap-4 overflow-y-auto p-4">
            <AlertaFormulario mensagem={errors.root?.message} />
            <Campo id="par-familia" rotulo="Família" erro={errors.id_familia?.message}>
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
            <div className="grid gap-4 sm:grid-cols-2">
              <Campo id="par-codigo" rotulo="Código" erro={errors.codigo?.message}>
                <Input placeholder="P0305" {...form.register("codigo")} />
              </Campo>
              <Campo id="par-idioma" rotulo="Idioma" erro={errors.idioma?.message}>
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
            <Campo id="par-descricao" rotulo="Descrição" erro={errors.descricao?.message}>
              <Textarea rows={3} placeholder="Corrente nominal do motor" {...form.register("descricao")} />
            </Campo>
            <div className="grid gap-4 sm:grid-cols-2">
              <Campo id="par-nome" rotulo="Nome" erro={errors.nome?.message}>
                <Input placeholder="Corrente nominal" {...form.register("nome")} />
              </Campo>
              <Campo id="par-grupo" rotulo="Grupo" erro={errors.grupo?.message}>
                <Input placeholder="Motor" {...form.register("grupo")} />
              </Campo>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <Campo id="par-min" rotulo="Valor mínimo" erro={errors.valor_min?.message}>
                <Input inputMode="decimal" placeholder="0" {...form.register("valor_min")} />
              </Campo>
              <Campo id="par-max" rotulo="Valor máximo" erro={errors.valor_max?.message}>
                <Input inputMode="decimal" placeholder="1000" {...form.register("valor_max")} />
              </Campo>
              <Campo id="par-unidade" rotulo="Unidade" erro={errors.unidade?.message}>
                <Input placeholder="A" {...form.register("unidade")} />
              </Campo>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Campo id="par-padrao" rotulo="Valor padrão" erro={errors.valor_padrao?.message}>
                <Input placeholder="0.0" {...form.register("valor_padrao")} />
              </Campo>
              <Campo id="par-firmware" rotulo="Versão de firmware" erro={errors.versao_firmware?.message}>
                <Input placeholder="4.7 SP14" {...form.register("versao_firmware")} />
              </Campo>
            </div>
            <Campo id="par-documento" rotulo="Documento de origem" erro={errors.id_documento?.message}>
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
            <Campo id="par-pagina" rotulo="Página no documento" erro={errors.pagina?.message}>
              <Input inputMode="numeric" placeholder="128" {...form.register("pagina")} />
            </Campo>
            <div className="grid gap-1.5">
              <Label>Somente leitura</Label>
              <Controller
                control={form.control}
                name="somente_leitura"
                render={({ field }) => (
                  <label className="flex h-9 items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      className="size-4 accent-primary"
                      checked={field.value}
                      onChange={(e) => {
                        field.onChange(e.target.checked);
                      }}
                      onBlur={field.onBlur}
                      ref={field.ref}
                    />
                    Não pode ser alterado no equipamento
                  </label>
                )}
              />
            </div>
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
