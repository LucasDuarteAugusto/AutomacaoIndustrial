import { Loader2 } from "lucide-react";
import { useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface ConfirmarExclusaoProps {
  aberto: boolean;
  aoMudar: (aberto: boolean) => void;
  titulo: string;
  descricao: ReactNode;
  rotuloConfirmar?: string;
  /** Rejeitar mantém o diálogo aberto (o chamador mostra o erro). */
  aoConfirmar: () => Promise<void>;
}

export function ConfirmarExclusao({
  aberto,
  aoMudar,
  titulo,
  descricao,
  rotuloConfirmar = "Excluir",
  aoConfirmar,
}: ConfirmarExclusaoProps) {
  const [executando, setExecutando] = useState(false);

  async function confirmar() {
    setExecutando(true);
    try {
      await aoConfirmar();
      aoMudar(false);
    } catch {
      // Mensagem tratada por quem chamou.
    } finally {
      setExecutando(false);
    }
  }

  return (
    <Dialog open={aberto} onOpenChange={(valor) => !executando && aoMudar(valor)}>
      <DialogContent className="sm:max-w-md" showCloseButton={!executando}>
        <DialogHeader>
          <DialogTitle>{titulo}</DialogTitle>
          <DialogDescription>{descricao}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            variant="outline"
            disabled={executando}
            onClick={() => {
              aoMudar(false);
            }}
          >
            Cancelar
          </Button>
          <Button variant="destructive" disabled={executando} onClick={() => void confirmar()}>
            {executando && <Loader2 className="animate-spin" />}
            {rotuloConfirmar}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
