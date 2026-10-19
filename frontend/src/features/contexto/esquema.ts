import { z } from "zod";

import { Idioma, TipoDocumento } from "@/api/gerado/modelos";

/** Filtros de contexto (fabricante → família → equipamento, tipo, idioma, firmware) guardados na URL. */
export const esquemaContexto = z.object({
  id_fabricante: z.uuid().optional().catch(undefined),
  id_familia: z.uuid().optional().catch(undefined),
  id_equipamento: z.uuid().optional().catch(undefined),
  tipo_documento: z.enum(TipoDocumento).optional().catch(undefined),
  idioma: z.enum(Idioma).optional().catch(undefined),
  versao_firmware: z
    .string()
    .trim()
    .max(30)
    .transform((valor) => (valor === "" ? undefined : valor))
    .optional()
    .catch(undefined),
});

export type Contexto = z.infer<typeof esquemaContexto>;

export const CHAVES_CONTEXTO = [
  "id_fabricante",
  "id_familia",
  "id_equipamento",
  "tipo_documento",
  "idioma",
  "versao_firmware",
] as const satisfies readonly (keyof Contexto)[];

export function contarFiltros(contexto: Contexto): number {
  return CHAVES_CONTEXTO.filter((chave) => contexto[chave] !== undefined).length;
}

/** Só os filtros preenchidos, no formato do corpo de `/v1/busca` e `/v1/agente/perguntar`. */
export function filtrosParaRequisicao(contexto: Contexto) {
  return {
    id_fabricante: contexto.id_fabricante ?? null,
    id_familia: contexto.id_familia ?? null,
    id_equipamento: contexto.id_equipamento ?? null,
    tipo_documento: contexto.tipo_documento ?? null,
    idioma: contexto.idioma ?? null,
    versao_firmware: contexto.versao_firmware ?? null,
  };
}
