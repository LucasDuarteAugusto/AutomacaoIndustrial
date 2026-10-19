import { Bot, Check, Copy, RotateCw, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import type { CitacaoOut } from "@/api/gerado/modelos";
import { MarkdownResposta } from "@/components/markdown-resposta";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

import { contarFiltros } from "../contexto/esquema";
import { CartaoFalha, CartaoParametro, type DestinoPdf } from "./cartoes";
import type { Turno } from "./historico";

interface TurnoConversaProps {
  turno: Turno;
  pendente: boolean;
  aoAbrirCitacao: (citacao: CitacaoOut) => void;
  aoAbrirPdf: (destino: DestinoPdf, titulo?: string) => void;
  aoRepetir: (turno: Turno) => void;
  aoRemover: (id: string) => void;
}

function useSegundosDecorridos(ativo: boolean): number {
  const [segundos, setSegundos] = useState(0);
  useEffect(() => {
    if (!ativo) return;
    const inicio = Date.now();
    const id = window.setInterval(() => {
      setSegundos(Math.floor((Date.now() - inicio) / 1000));
    }, 1000);
    return () => {
      window.clearInterval(id);
      setSegundos(0);
    };
  }, [ativo]);
  return segundos;
}

function BotaoCopiar({ texto }: { texto: string }) {
  const [copiado, setCopiado] = useState(false);
  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => {
        void navigator.clipboard.writeText(texto).then(() => {
          setCopiado(true);
          window.setTimeout(() => {
            setCopiado(false);
          }, 1500);
        });
      }}
    >
      {copiado ? <Check /> : <Copy />} {copiado ? "Copiado" : "Copiar"}
    </Button>
  );
}

export function TurnoConversa({
  turno,
  pendente,
  aoAbrirCitacao,
  aoAbrirPdf,
  aoRepetir,
  aoRemover,
}: TurnoConversaProps) {
  const [destacado, setDestacado] = useState<string | null>(null);
  const segundos = useSegundosDecorridos(pendente);
  const { resposta } = turno;
  const parametros = resposta?.parametros ?? [];
  const falhas = resposta?.falhas ?? [];
  const citacoes = resposta?.citacoes ?? [];
  const filtros = contarFiltros(turno.contexto);

  const marcasValidas = new Set<string>([
    ...citacoes.map((c) => String(c.indice)),
    ...parametros.map((_p, i) => `P${i + 1}`),
    ...falhas.map((_f, i) => `F${i + 1}`),
  ]);

  const tituloDoDocumento = (idDocumento: string) =>
    citacoes.find((c) => c.id_documento === idDocumento)?.titulo_documento;

  const aoClicarMarca = (marca: string) => {
    if (/^\d+$/.test(marca)) {
      const citacao = citacoes.find((c) => String(c.indice) === marca);
      if (citacao) aoAbrirCitacao(citacao);
      return;
    }
    setDestacado(marca);
    document.getElementById(`${turno.id}-${marca}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
    window.setTimeout(() => {
      setDestacado(null);
    }, 2000);
  };

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-primary px-4 py-2.5 text-sm whitespace-pre-wrap text-primary-foreground">
          {turno.pergunta}
          {filtros > 0 && (
            <span className="mt-1 block text-xs opacity-75">
              Com contexto ({filtros} filtro{filtros > 1 ? "s" : ""})
            </span>
          )}
        </div>
      </div>

      <div className="flex gap-3">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-muted" aria-hidden>
          <Bot className="size-4" />
        </div>
        <div className="min-w-0 flex-1 space-y-4">
          {pendente && (
            <div className="space-y-2" role="status" aria-live="polite">
              <p className="text-sm text-muted-foreground">
                {segundos < 4 ? "Buscando nos manuais…" : "Gerando a resposta…"} ({segundos}s)
              </p>
              <Skeleton className="h-4 w-11/12" />
              <Skeleton className="h-4 w-9/12" />
              <Skeleton className="h-4 w-10/12" />
            </div>
          )}

          {turno.erro && !pendente && (
            <Alert variant="destructive">
              <AlertDescription className="flex flex-wrap items-center gap-3">
                <span>{turno.erro}</span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    aoRepetir(turno);
                  }}
                >
                  <RotateCw /> Perguntar de novo
                </Button>
              </AlertDescription>
            </Alert>
          )}

          {resposta && (
            <>
              <MarkdownResposta
                texto={resposta.resposta}
                marcasValidas={marcasValidas}
                aoClicarMarca={aoClicarMarca}
              />

              {parametros.length > 0 && (
                <section aria-label="Parâmetros encontrados" className="space-y-2">
                  <h3 className="text-sm font-semibold">Parâmetros</h3>
                  {parametros.map((parametro, i) => (
                    <CartaoParametro
                      key={parametro.id_parametro}
                      id={`${turno.id}-P${i + 1}`}
                      marca={`P${i + 1}`}
                      parametro={parametro}
                      destacado={destacado === `P${i + 1}`}
                      aoAbrirPdf={(d) => {
                        aoAbrirPdf(d, tituloDoDocumento(d.idDocumento));
                      }}
                    />
                  ))}
                </section>
              )}

              {falhas.length > 0 && (
                <section aria-label="Falhas e alarmes encontrados" className="space-y-2">
                  <h3 className="text-sm font-semibold">Falhas e alarmes</h3>
                  {falhas.map((falha, i) => (
                    <CartaoFalha
                      key={falha.id_falha}
                      id={`${turno.id}-F${i + 1}`}
                      marca={`F${i + 1}`}
                      falha={falha}
                      destacado={destacado === `F${i + 1}`}
                      aoAbrirPdf={(d) => {
                        aoAbrirPdf(d, tituloDoDocumento(d.idDocumento));
                      }}
                    />
                  ))}
                </section>
              )}

              {citacoes.length > 0 && (
                <section aria-label="Fontes" className="space-y-2">
                  <h3 className="text-sm font-semibold">Fontes</h3>
                  <ol className="grid gap-1">
                    {citacoes.map((citacao) => (
                      <li key={citacao.id_trecho}>
                        <button
                          type="button"
                          className="flex w-full items-baseline gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-muted"
                          onClick={() => {
                            aoAbrirCitacao(citacao);
                          }}
                        >
                          <span className="font-mono text-xs font-semibold text-primary">
                            [{citacao.indice}]
                          </span>
                          <span className="min-w-0 flex-1 truncate">{citacao.titulo_documento}</span>
                          {citacao.pagina !== null && (
                            <span className="shrink-0 text-xs text-muted-foreground">
                              p. {citacao.pagina}
                            </span>
                          )}
                        </button>
                      </li>
                    ))}
                  </ol>
                </section>
              )}

              <footer className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <span>
                  {resposta.modelo_llm} · {resposta.trechos_consultados} trecho
                  {resposta.trechos_consultados === 1 ? "" : "s"} consultado
                  {resposta.trechos_consultados === 1 ? "" : "s"}
                </span>
                <div className="flex-1" />
                <BotaoCopiar texto={resposta.resposta} />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    aoRemover(turno.id);
                  }}
                >
                  <Trash2 /> Remover
                </Button>
              </footer>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
