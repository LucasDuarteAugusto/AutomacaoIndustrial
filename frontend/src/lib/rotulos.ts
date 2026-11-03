import { z } from "zod";

import type {
  Idioma,
  Perfil,
  StatusProcessamento,
  TipoConteudo,
  TipoDocumento,
  TipoFalha,
} from "@/api/gerado/modelos";

export const ROTULO_PERFIL: Record<Perfil, string> = {
  ADMIN: "Administrador",
  OPERADOR: "Operador",
  LEITURA: "Leitura",
};

export const ROTULO_TIPO_DOCUMENTO: Record<TipoDocumento, string> = {
  MANUAL_OPERACAO: "Manual de operação",
  LISTA_PARAMETROS: "Lista de parâmetros",
  GUIA_RAPIDO: "Guia rápido",
  MANUAL_COMUNICACAO: "Manual de comunicação",
  DATASHEET: "Datasheet",
  NOTA_APLICACAO: "Nota de aplicação",
};

export const ROTULO_IDIOMA: Record<Idioma, string> = {
  "pt-BR": "Português",
  en: "Inglês",
};

export const ROTULO_STATUS: Record<StatusProcessamento, string> = {
  PENDENTE: "Pendente",
  PROCESSANDO: "Processando",
  INDEXADO: "Indexado",
  ERRO: "Erro",
};

export const ROTULO_TIPO_FALHA: Record<TipoFalha, string> = {
  FALHA: "Falha",
  ALARME: "Alarme",
};

export const ROTULO_TIPO_CONTEUDO: Record<TipoConteudo, string> = {
  TEXTO: "Texto",
  TABELA: "Tabela",
  LISTA: "Lista",
  LEGENDA_FIGURA: "Legenda de figura",
  CODIGO: "Código",
};

export const TIPOS_DOCUMENTO = Object.keys(ROTULO_TIPO_DOCUMENTO) as TipoDocumento[];
export const IDIOMAS = Object.keys(ROTULO_IDIOMA) as Idioma[];
export const STATUS_PROCESSAMENTO = Object.keys(ROTULO_STATUS) as StatusProcessamento[];
export const TIPOS_FALHA = Object.keys(ROTULO_TIPO_FALHA) as TipoFalha[];
export const PERFIS = Object.keys(ROTULO_PERFIL) as Perfil[];

/** Valores de filtro `ativo` na URL (query string). */
export const FILTRO_ATIVO = ["true", "false"] as const;
export type FiltroAtivo = (typeof FILTRO_ATIVO)[number];
export const ROTULO_FILTRO_ATIVO: Record<FiltroAtivo, string> = {
  true: "Ativos",
  false: "Inativos",
};

/**
 * Schema para o filtro `ativo` na URL. O router desserializa `?ativo=true` como boolean,
 * então normalizamos de volta para o texto do enum.
 */
export const esquemaFiltroAtivo = z.preprocess(
  (valor) => (typeof valor === "boolean" ? String(valor) : valor),
  z.enum(FILTRO_ATIVO).optional().catch(undefined),
);

export function ativoDaUrl(valor: FiltroAtivo | boolean | undefined): boolean | undefined {
  if (valor === true || valor === "true") return true;
  if (valor === false || valor === "false") return false;
  return undefined;
}
