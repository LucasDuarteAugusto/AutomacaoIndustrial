import { useEffect } from "react";
import { toast } from "sonner";

import { encerrarSessao } from "./sessao";

const AVISO_ANTES_MS = 10 * 60_000;

export function useAvisoExpiracao(expiraEm: number | undefined) {
  useEffect(() => {
    if (!expiraEm) return;
    const agora = Date.now();
    const timers: number[] = [];
    const faltaAviso = expiraEm - AVISO_ANTES_MS - agora;
    if (faltaAviso > 0) {
      timers.push(
        window.setTimeout(() => {
          toast.warning("Sua sessão expira em 10 minutos. Salve o que estiver fazendo e entre novamente.", {
            duration: 30_000,
          });
        }, faltaAviso),
      );
    }
    timers.push(
      window.setTimeout(
        () => {
          encerrarSessao("expirada");
        },
        Math.max(0, expiraEm - agora),
      ),
    );
    return () => {
      timers.forEach((id) => {
        window.clearTimeout(id);
      });
    };
  }, [expiraEm]);
}
