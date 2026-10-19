import { CircleAlert, RotateCw } from "lucide-react";

import { mensagemDeErro } from "@/api/problema";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

/** Erro de consulta com mensagem amigável e opção de tentar de novo. */
export function ProblemaAlerta({
  erro,
  titulo = "Não foi possível carregar os dados",
  aoTentarDeNovo,
}: {
  erro: unknown;
  titulo?: string;
  aoTentarDeNovo?: () => void;
}) {
  return (
    <Alert variant="destructive">
      <CircleAlert />
      <AlertTitle>{titulo}</AlertTitle>
      <AlertDescription className="flex flex-wrap items-center gap-3">
        <span>{mensagemDeErro(erro)}</span>
        {aoTentarDeNovo && (
          <Button size="sm" variant="outline" onClick={aoTentarDeNovo}>
            <RotateCw /> Tentar de novo
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}
