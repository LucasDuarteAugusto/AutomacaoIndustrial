import { CircleAlert } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";

export function AlertaFormulario({ mensagem }: { mensagem: string | undefined }) {
  if (!mensagem) return null;
  return (
    <Alert variant="destructive">
      <CircleAlert />
      <AlertDescription>{mensagem}</AlertDescription>
    </Alert>
  );
}
