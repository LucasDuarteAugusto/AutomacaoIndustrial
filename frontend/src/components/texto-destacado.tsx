function escaparRegex(texto: string): string {
  return texto.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Realça no texto as palavras da consulta (3+ letras, sem diferenciar maiúsculas). */
export function TextoDestacado({ texto, consulta }: { texto: string; consulta: string }) {
  const termos = [...new Set(consulta.toLowerCase().split(/\s+/))].filter((t) => t.length >= 3);
  if (termos.length === 0) return <>{texto}</>;
  const padrao = new RegExp(`(${termos.map(escaparRegex).join("|")})`, "gi");
  return (
    <>
      {texto.split(padrao).map((parte, i) =>
        i % 2 === 1 ? (
          <mark key={i} className="rounded-sm bg-aviso/40 px-0.5 text-foreground">
            {parte}
          </mark>
        ) : (
          parte
        ),
      )}
    </>
  );
}
