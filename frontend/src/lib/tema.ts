import { useCallback, useSyncExternalStore } from "react";

export type Tema = "claro" | "escuro";

const ouvintes = new Set<() => void>();

function temaAtual(): Tema {
  return document.documentElement.classList.contains("dark") ? "escuro" : "claro";
}

function assinar(ouvinte: () => void) {
  ouvintes.add(ouvinte);
  return () => ouvintes.delete(ouvinte);
}

export function useTema(): [Tema, () => void] {
  const tema = useSyncExternalStore(assinar, temaAtual);
  const alternar = useCallback(() => {
    const novo: Tema = temaAtual() === "escuro" ? "claro" : "escuro";
    document.documentElement.classList.toggle("dark", novo === "escuro");
    localStorage.setItem("tema", novo);
    for (const ouvinte of ouvintes) ouvinte();
  }, []);
  return [tema, alternar];
}
