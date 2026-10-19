import { useCallback, useState } from "react";

import type { AgenteRespostaOut } from "@/api/gerado/modelos";

import type { Contexto } from "../contexto/esquema";

export interface Turno {
  id: string;
  pergunta: string;
  contexto: Contexto;
  criadoEm: string;
  resposta?: AgenteRespostaOut;
  erro?: string;
}

const CHAVE = "automacao.assistente.historico";
const MAXIMO = 20;

function carregar(): Turno[] {
  try {
    const bruto = sessionStorage.getItem(CHAVE);
    return bruto ? (JSON.parse(bruto) as Turno[]) : [];
  } catch {
    return [];
  }
}

/** Conversa da aba atual (sessionStorage) até o backend ter histórico por usuário. */
export function useHistorico() {
  const [turnos, setTurnos] = useState<Turno[]>(carregar);

  const salvar = useCallback((atualizar: (atuais: Turno[]) => Turno[]) => {
    setTurnos((atuais) => {
      const novos = atualizar(atuais).slice(-MAXIMO);
      sessionStorage.setItem(CHAVE, JSON.stringify(novos));
      return novos;
    });
  }, []);

  const adicionar = useCallback(
    (turno: Turno) => {
      salvar((atuais) => [...atuais, turno]);
    },
    [salvar],
  );

  const atualizar = useCallback(
    (id: string, parcial: Partial<Turno>) => {
      salvar((atuais) => atuais.map((t) => (t.id === id ? { ...t, ...parcial } : t)));
    },
    [salvar],
  );

  const remover = useCallback(
    (id: string) => {
      salvar((atuais) => atuais.filter((t) => t.id !== id));
    },
    [salvar],
  );

  const limpar = useCallback(() => {
    salvar(() => []);
  }, [salvar]);

  return { turnos, adicionar, atualizar, remover, limpar };
}
