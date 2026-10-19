import type { QueryClient } from "@tanstack/react-query";

import {
  getBaixarArquivoDocumentoQueryKey,
  getListarDocumentosQueryKey,
  getObterDocumentoQueryKey,
} from "@/api/gerado/documentos/documentos";
import type { DocumentoOut } from "@/api/gerado/modelos";

/** Atualiza o detalhe com a resposta da API e marca as listas como desatualizadas. */
export function documentoAtualizado(
  queryClient: QueryClient,
  documento: DocumentoOut,
  { arquivoMudou = false } = {},
) {
  queryClient.setQueryData(getObterDocumentoQueryKey(documento.id_documento), documento);
  void queryClient.invalidateQueries({ queryKey: getListarDocumentosQueryKey() });
  if (arquivoMudou)
    queryClient.removeQueries({ queryKey: getBaixarArquivoDocumentoQueryKey(documento.id_documento) });
}

export function documentoRemovido(queryClient: QueryClient, idDocumento: string) {
  queryClient.removeQueries({ queryKey: getObterDocumentoQueryKey(idDocumento) });
  queryClient.removeQueries({ queryKey: getBaixarArquivoDocumentoQueryKey(idDocumento) });
  void queryClient.invalidateQueries({ queryKey: getListarDocumentosQueryKey() });
}

export function estaProcessando(
  documento: Pick<DocumentoOut, "status_processamento" | "chave_arquivo">,
): boolean {
  if (!documento.chave_arquivo) return false;
  return documento.status_processamento === "PENDENTE" || documento.status_processamento === "PROCESSANDO";
}
