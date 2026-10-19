import { useMutation } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Eraser, Send, Square } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { perguntar } from "@/api/gerado/agente/agente";
import type { AgentePerguntaRequest, CitacaoOut } from "@/api/gerado/modelos";
import { ehProblema, mensagemDeErro } from "@/api/problema";
import { AvisoLimite } from "@/components/aviso-limite";
import { CabecalhoPagina } from "@/components/cabecalho-pagina";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { type PdfAberto, VisualizadorPdf } from "@/components/visualizador-pdf";
import type { DestinoPdf } from "@/features/agente/cartoes";
import { type Turno, useHistorico } from "@/features/agente/historico";
import { PainelCitacao } from "@/features/agente/painel-citacao";
import { TurnoConversa } from "@/features/agente/turno";
import { esquemaContexto, filtrosParaRequisicao } from "@/features/contexto/esquema";
import { FiltrosContexto } from "@/features/contexto/filtros-contexto";

const MAX_PERGUNTA = 2000;

const SUGESTOES = [
  "Qual parâmetro ajusta o tempo de rampa de aceleração no SINAMICS G120?",
  "O que significa a falha F07801 e como resolver?",
  "Como configurar o SIMOCODE pro na rede PROFINET?",
];

export const Route = createFileRoute("/_app/assistente")({
  validateSearch: esquemaContexto,
  component: PaginaAssistente,
});

function ehCancelamento(erro: unknown): boolean {
  return erro instanceof DOMException && erro.name === "AbortError";
}

function PaginaAssistente() {
  const contexto = Route.useSearch();
  const navigate = Route.useNavigate();
  const { turnos, adicionar, atualizar, remover, limpar } = useHistorico();
  const [pergunta, setPergunta] = useState("");
  const [pendenteId, setPendenteId] = useState<string | null>(null);
  const [limite, setLimite] = useState<{ segundos: number; chave: number } | null>(null);
  const [citacao, setCitacao] = useState<CitacaoOut | null>(null);
  const [pdf, setPdf] = useState<PdfAberto | null>(null);
  const controlador = useRef<AbortController | null>(null);
  const fimDaConversa = useRef<HTMLDivElement>(null);
  const liberarLimite = useCallback(() => {
    setLimite(null);
  }, []);

  const mutacao = useMutation({
    mutationFn: ({ dados, signal }: { dados: AgentePerguntaRequest; signal: AbortSignal }) =>
      perguntar(dados, { signal }),
  });

  useEffect(() => {
    fimDaConversa.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turnos.length, pendenteId]);

  useEffect(() => () => controlador.current?.abort(), []);

  async function enviar(texto: string) {
    const limpo = texto.trim();
    if (!limpo || pendenteId || limite) return;
    const id = crypto.randomUUID();
    adicionar({ id, pergunta: limpo, contexto, criadoEm: new Date().toISOString() });
    setPergunta("");
    setPendenteId(id);
    const ctrl = new AbortController();
    controlador.current = ctrl;
    try {
      const resposta = await mutacao.mutateAsync({
        dados: { pergunta: limpo, ...filtrosParaRequisicao(contexto) },
        signal: ctrl.signal,
      });
      atualizar(id, { resposta });
    } catch (erro) {
      if (ehCancelamento(erro)) {
        atualizar(id, { erro: "Pergunta cancelada." });
      } else {
        if (ehProblema(erro, 429)) setLimite({ segundos: erro.retryAfter ?? 60, chave: Date.now() });
        atualizar(id, { erro: mensagemDeErro(erro) });
      }
    } finally {
      setPendenteId(null);
      controlador.current = null;
    }
  }

  function repetir(turno: Turno) {
    remover(turno.id);
    void enviar(turno.pergunta);
  }

  function abrirPdf(destino: DestinoPdf, titulo?: string) {
    setPdf({
      idDocumento: destino.idDocumento,
      titulo: titulo ?? "Documento",
      paginaInicial: destino.pagina,
      rotuloPagina: destino.pagina ? `Aberto na página ${destino.pagina}` : undefined,
    });
  }

  const desabilitado = pendenteId !== null || limite !== null;

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-4">
      <CabecalhoPagina
        titulo="Assistente"
        descricao="Pergunte sobre parâmetros, falhas e procedimentos. As respostas citam os manuais cadastrados."
        acoes={
          turnos.length > 0 && (
            <Button variant="outline" size="sm" onClick={limpar} disabled={pendenteId !== null}>
              <Eraser /> Limpar conversa
            </Button>
          )
        }
      />

      <FiltrosContexto
        contexto={contexto}
        aoMudar={(novo) => {
          void navigate({ search: novo, replace: true });
        }}
      />

      <div className="space-y-8 py-2" aria-live="polite">
        {turnos.length === 0 && (
          <div className="space-y-3 py-8 text-center text-sm text-muted-foreground">
            <p>Comece com uma pergunta. Alguns exemplos:</p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGESTOES.map((sugestao) => (
                <Button
                  key={sugestao}
                  variant="outline"
                  size="sm"
                  className="h-auto py-2 whitespace-normal"
                  onClick={() => {
                    setPergunta(sugestao);
                  }}
                >
                  {sugestao}
                </Button>
              ))}
            </div>
          </div>
        )}
        {turnos.map((turno) => (
          <TurnoConversa
            key={turno.id}
            turno={turno}
            pendente={turno.id === pendenteId}
            aoAbrirCitacao={setCitacao}
            aoAbrirPdf={abrirPdf}
            aoRepetir={repetir}
            aoRemover={remover}
          />
        ))}
        <div ref={fimDaConversa} />
      </div>

      <form
        className="sticky bottom-0 space-y-2 border-t bg-background pt-3 pb-2"
        onSubmit={(e) => {
          e.preventDefault();
          void enviar(pergunta);
        }}
      >
        {limite && <AvisoLimite key={limite.chave} segundos={limite.segundos} aoTerminar={liberarLimite} />}
        <label htmlFor="pergunta" className="sr-only">
          Pergunta
        </label>
        <Textarea
          id="pergunta"
          value={pergunta}
          maxLength={MAX_PERGUNTA}
          rows={3}
          placeholder="Ex.: qual parâmetro define a corrente nominal do motor? (Enter envia, Shift+Enter quebra linha)"
          onChange={(e) => {
            setPergunta(e.target.value);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              void enviar(pergunta);
            }
          }}
          className="resize-none"
        />
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground tabular-nums">
            {pergunta.length}/{MAX_PERGUNTA}
          </span>
          <div className="flex-1" />
          {pendenteId ? (
            <Button type="button" variant="outline" onClick={() => controlador.current?.abort()}>
              <Square /> Cancelar
            </Button>
          ) : (
            <Button type="submit" disabled={desabilitado || !pergunta.trim()}>
              <Send /> Perguntar
            </Button>
          )}
        </div>
      </form>

      <PainelCitacao
        citacao={citacao}
        aoFechar={() => {
          setCitacao(null);
        }}
        aoAbrirPdf={(destino) => {
          abrirPdf(destino, citacao?.titulo_documento);
        }}
      />
      <VisualizadorPdf
        pdf={pdf}
        aoFechar={() => {
          setPdf(null);
        }}
      />
    </div>
  );
}
