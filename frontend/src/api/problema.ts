import type { FieldValues, Path, UseFormSetError } from "react-hook-form";

export interface ErroCampo {
  loc: (string | number)[];
  msg: string;
  type: string;
}

interface DadosProblema {
  status: number;
  titulo: string;
  detalhe?: string | null;
  erros?: ErroCampo[];
  retryAfter?: number;
}

/** Erro RFC 9457 (application/problem+json) devolvido pela API. `status` 0 = falha de rede. */
export class ProblemaApi extends Error {
  readonly status: number;
  readonly titulo: string;
  readonly detalhe: string | null;
  readonly erros: ErroCampo[];
  readonly retryAfter: number | undefined;

  constructor({ status, titulo, detalhe = null, erros = [], retryAfter }: DadosProblema) {
    super(detalhe ?? titulo);
    this.name = "ProblemaApi";
    this.status = status;
    this.titulo = titulo;
    this.detalhe = detalhe;
    this.erros = erros;
    this.retryAfter = retryAfter;
  }
}

interface CorpoProblema {
  title?: string;
  detail?: string | null;
  errors?: ErroCampo[];
}

export async function problemaDaResposta(resposta: Response): Promise<ProblemaApi> {
  const corpo = (await resposta.json().catch(() => null)) as CorpoProblema | null;
  const retryAfter = Number(resposta.headers.get("Retry-After"));
  return new ProblemaApi({
    status: resposta.status,
    titulo: corpo?.title ?? (resposta.statusText || `Erro ${resposta.status}`),
    detalhe: corpo?.detail ?? null,
    erros: Array.isArray(corpo?.errors) ? corpo.errors : [],
    retryAfter: Number.isFinite(retryAfter) && retryAfter > 0 ? retryAfter : undefined,
  });
}

export function ehProblema(erro: unknown, status?: number): erro is ProblemaApi {
  return erro instanceof ProblemaApi && (status === undefined || erro.status === status);
}

/** Texto curto para toast/alerta, a partir de qualquer erro. */
export function mensagemDeErro(erro: unknown): string {
  if (!(erro instanceof ProblemaApi)) return "Erro inesperado. Tente novamente.";
  switch (erro.status) {
    case 0:
      return erro.detalhe ?? erro.titulo;
    case 403:
      return "Seu perfil não permite esta ação.";
    case 429:
      return `Muitas requisições. Tente novamente em ${erro.retryAfter ?? 60} s.`;
    default:
      if (erro.status >= 500) return "Erro no servidor. Tente novamente em instantes.";
      return erro.detalhe ?? erro.titulo;
  }
}

/**
 * Leva os erros 422 (`loc: ["body", "campo"]`) para os campos do formulário.
 * Retorna true se algum campo recebeu erro; senão o chamador mostra a mensagem geral.
 */
export function aplicarErrosNoFormulario<T extends FieldValues>(
  erro: unknown,
  setError: UseFormSetError<T>,
  campos: readonly Path<T>[],
): boolean {
  if (!ehProblema(erro, 422)) return false;
  let aplicou = false;
  for (const item of erro.erros) {
    const [origem, campo] = item.loc;
    if (origem === "body" && typeof campo === "string" && (campos as readonly string[]).includes(campo)) {
      setError(campo as Path<T>, { type: "servidor", message: item.msg });
      aplicou = true;
    }
  }
  return aplicou;
}
