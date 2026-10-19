import { QueryClient } from "@tanstack/react-query";

import { ehProblema, ProblemaApi } from "@/api/problema";

function deveTentarDeNovo(falhas: number, erro: unknown): boolean {
  if (ehProblema(erro, 429)) return falhas < 1;
  if (erro instanceof ProblemaApi && erro.status >= 400 && erro.status < 500) return false;
  return falhas < 2;
}

function atrasoAntesDeTentar(falhas: number, erro: unknown): number {
  if (ehProblema(erro, 429)) return (erro.retryAfter ?? 5) * 1000;
  return Math.min(1000 * 2 ** falhas, 8000);
}

export function criarQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        refetchOnWindowFocus: false,
        retry: deveTentarDeNovo,
        retryDelay: atrasoAntesDeTentar,
      },
      mutations: { retry: false },
    },
  });
}
