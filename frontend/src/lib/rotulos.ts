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
