import { ChevronDown, ChevronUp, FileText } from "lucide-react";
import { useState } from "react";

import type { TrechoBuscaOut } from "@/api/gerado/modelos";
import { CodigoCopiavel } from "@/components/codigo-copiavel";
import { TextoDestacado } from "@/components/texto-destacado";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ROTULO_IDIOMA, ROTULO_TIPO_CONTEUDO, ROTULO_TIPO_DOCUMENTO } from "@/lib/rotulos";
import { cn } from "@/lib/utils";

const LIMITE_RECOLHIDO = 600;

export function ResultadoTrecho({
  trecho,
  posicao,
  consulta,
  aoAbrirPdf,
}: {
  trecho: TrechoBuscaOut;
  posicao: number;
  consulta: string;
  aoAbrirPdf: (trecho: TrechoBuscaOut) => void;
}) {
  const [expandido, setExpandido] = useState(false);
  const longo = trecho.conteudo.length > LIMITE_RECOLHIDO;
  const conteudo = longo && !expandido ? `${trecho.conteudo.slice(0, LIMITE_RECOLHIDO)}…` : trecho.conteudo;

  return (
    <article className="space-y-3 rounded-lg border bg-card p-4">
      <header className="space-y-1.5">
        <div className="flex flex-wrap items-baseline gap-2">
          <span className="font-mono text-xs text-muted-foreground">#{posicao}</span>
          <h2 className="font-medium">{trecho.titulo_documento}</h2>
          {trecho.codigo_documento && <CodigoCopiavel codigo={trecho.codigo_documento} className="text-xs" />}
        </div>
        <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
          <Badge variant="secondary">{ROTULO_TIPO_DOCUMENTO[trecho.tipo_documento]}</Badge>
          <Badge variant="outline">{ROTULO_IDIOMA[trecho.idioma]}</Badge>
          <Badge variant="outline">{ROTULO_TIPO_CONTEUDO[trecho.tipo_conteudo]}</Badge>
          {trecho.versao_firmware && <span>Firmware {trecho.versao_firmware}</span>}
          {trecho.secao && <span>· Seção: {trecho.secao}</span>}
          {trecho.pagina !== null && <span>· Página {trecho.pagina}</span>}
          <span className="tabular-nums" title="Pontuação RRF (semântica + textual)">
            · Relevância {trecho.score.toFixed(3)}
          </span>
        </div>
      </header>
      <p className={cn("text-sm leading-relaxed whitespace-pre-wrap")}>
        <TextoDestacado texto={conteudo} consulta={consulta} />
      </p>
      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            aoAbrirPdf(trecho);
          }}
        >
          <FileText /> Abrir PDF{trecho.pagina !== null ? ` na página ${trecho.pagina}` : ""}
        </Button>
        {longo && (
          <Button
            size="sm"
            variant="ghost"
            aria-expanded={expandido}
            onClick={() => {
              setExpandido((valor) => !valor);
            }}
          >
            {expandido ? <ChevronUp /> : <ChevronDown />} {expandido ? "Ver menos" : "Ver trecho completo"}
          </Button>
        )}
      </div>
    </article>
  );
}
