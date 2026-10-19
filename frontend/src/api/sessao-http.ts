/**
 * Ponte entre o cliente HTTP e a sessão: o cliente lê o token e avisa sobre 401
 * sem importar React nem o módulo de sessão (evita dependência circular).
 */
let lerToken: () => string | null = () => null;
let tratarNaoAutorizado: () => void = () => undefined;

export function configurarSessaoHttp(opcoes: {
  obterToken: () => string | null;
  aoNaoAutorizado: () => void;
}) {
  lerToken = opcoes.obterToken;
  tratarNaoAutorizado = opcoes.aoNaoAutorizado;
}

export function obterToken(): string | null {
  return lerToken();
}

export function aoNaoAutorizado(): void {
  tratarNaoAutorizado();
}
