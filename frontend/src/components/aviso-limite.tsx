import { Timer } from "lucide-react";
import { useEffect, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";

/** Contagem regressiva do `Retry-After` de um 429. Remonte (via `key`) a cada novo bloqueio. */
export function AvisoLimite({ segundos, aoTerminar }: { segundos: number; aoTerminar: () => void }) {
  const [restante, setRestante] = useState(segundos);

  useEffect(() => {
    const id = window.setInterval(() => {
      setRestante((atual) => Math.max(0, atual - 1));
    }, 1000);
    return () => {
      window.clearInterval(id);
    };
  }, []);

  useEffect(() => {
    if (restante === 0) aoTerminar();
  }, [restante, aoTerminar]);

  return (
    <Alert>
      <Timer />
      <AlertDescription>Limite de requisições atingido. Tente de novo em {restante}s.</AlertDescription>
    </Alert>
  );
}
