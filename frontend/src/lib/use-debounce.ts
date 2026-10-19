import { useEffect, useState } from "react";

export function useDebounce<T>(valor: T, atrasoMs = 300): T {
  const [atrasado, setAtrasado] = useState(valor);
  useEffect(() => {
    const id = window.setTimeout(() => {
      setAtrasado(valor);
    }, atrasoMs);
    return () => {
      window.clearTimeout(id);
    };
  }, [valor, atrasoMs]);
  return atrasado;
}
