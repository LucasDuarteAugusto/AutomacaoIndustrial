import { ProblemaApi, problemaDaResposta } from "./problema";
import { aoNaoAutorizado, obterToken } from "./sessao-http";

// Lido pelo Orval: tipo de erro dos hooks gerados.
export type ErrorType<_Erro> = ProblemaApi;

export async function http<T>(url: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = obterToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!headers.has("Accept")) headers.set("Accept", "application/json");

  let resposta: Response;
  try {
    resposta = await fetch(url, { ...init, headers });
  } catch (erro) {
    if (erro instanceof DOMException && erro.name === "AbortError") throw erro;
    throw new ProblemaApi({
      status: 0,
      titulo: "Sem conexão",
      detalhe: "Não foi possível falar com o servidor.",
    });
  }

  if (!resposta.ok) {
    const problema = await problemaDaResposta(resposta);
    if (problema.status === 401 && token) aoNaoAutorizado();
    throw problema;
  }
  if (resposta.status === 204 || resposta.status === 304) return undefined as T;
  const tipo = resposta.headers.get("Content-Type") ?? "";
  return (tipo.includes("json") ? await resposta.json() : await resposta.blob()) as T;
}
