import type { DocumentoOut } from "./gerado/modelos";
import { ProblemaApi, type ErroCampo } from "./problema";
import { aoNaoAutorizado, obterToken } from "./sessao-http";

export const TAMANHO_MAX_PDF = 50 * 1024 * 1024;

interface OpcoesUpload {
  aoProgredir?: (percentual: number) => void;
  signal?: AbortSignal;
}

/** Validação local antes de enviar; o backend repete a checagem (assinatura %PDF-). */
export function validarArquivoPdf(arquivo: File): string | null {
  if (arquivo.size === 0) return "O arquivo está vazio.";
  if (arquivo.size > TAMANHO_MAX_PDF) return "O arquivo excede o limite de 50 MiB.";
  const ehPdf = arquivo.type === "application/pdf" || arquivo.name.toLowerCase().endsWith(".pdf");
  return ehPdf ? null : "Selecione um arquivo PDF.";
}

interface CorpoProblema {
  title?: string;
  detail?: string | null;
  errors?: ErroCampo[];
}

function lerCorpo(texto: string): CorpoProblema | null {
  try {
    return JSON.parse(texto) as CorpoProblema;
  } catch {
    return null;
  }
}

function problemaDoXhr(xhr: XMLHttpRequest): ProblemaApi {
  const corpo = lerCorpo(xhr.responseText);
  const retryAfter = Number(xhr.getResponseHeader("Retry-After"));
  return new ProblemaApi({
    status: xhr.status,
    titulo: corpo?.title ?? (xhr.statusText || `Erro ${xhr.status}`),
    detalhe: corpo?.detail ?? null,
    erros: corpo?.errors ?? [],
    retryAfter: Number.isFinite(retryAfter) && retryAfter > 0 ? retryAfter : undefined,
  });
}

/** `fetch` não informa progresso de envio; por isso o upload usa XMLHttpRequest. */
export function enviarPdfDocumento(
  idDocumento: string,
  arquivo: File,
  { aoProgredir, signal }: OpcoesUpload = {},
): Promise<DocumentoOut> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `/v1/documentos/${idDocumento}/arquivo`);
    const token = obterToken();
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.setRequestHeader("Accept", "application/json");

    xhr.upload.onprogress = (evento) => {
      if (evento.lengthComputable) aoProgredir?.(Math.round((evento.loaded / evento.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText) as DocumentoOut);
        return;
      }
      if (xhr.status === 401 && token) aoNaoAutorizado();
      reject(problemaDoXhr(xhr));
    };
    xhr.onerror = () => {
      reject(
        new ProblemaApi({ status: 0, titulo: "Sem conexão", detalhe: "Falha de rede durante o envio." }),
      );
    };
    xhr.onabort = () => {
      reject(new DOMException("Envio cancelado", "AbortError"));
    };
    signal?.addEventListener("abort", () => {
      xhr.abort();
    });

    const formulario = new FormData();
    formulario.append("arquivo", arquivo);
    xhr.send(formulario);
  });
}
