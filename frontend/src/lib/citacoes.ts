/** `[1]`, `[P2]`, `[F1]` e listas como `[1, 3]`, desde que não sejam links Markdown (`[x](url)`). */
const MARCAS = /\[((?:[PF]?\d+)(?:\s*,\s*[PF]?\d+)*)\](?!\()/g;

export const PREFIXO_CITACAO = "#citacao-";

/** Transforma as marcas de citação da resposta do agente em links internos tratados pelo renderizador. */
export function marcarCitacoes(texto: string): string {
  return texto.replace(MARCAS, (_trecho, grupo: string) =>
    grupo
      .split(/\s*,\s*/)
      .map((marca) => `[${marca}](${PREFIXO_CITACAO}${marca})`)
      .join(""),
  );
}
