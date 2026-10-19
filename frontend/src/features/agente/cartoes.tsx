import { FileText, Lock } from "lucide-react";

import type { FalhaOut, ParametroOut } from "@/api/gerado/modelos";
import { CodigoCopiavel } from "@/components/codigo-copiavel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatarNumero } from "@/lib/formato";
import { ROTULO_TIPO_FALHA } from "@/lib/rotulos";
import { cn } from "@/lib/utils";

export interface DestinoPdf {
  idDocumento: string;
  pagina: number | null;
}

function BotaoPdf({
  destino,
  aoAbrirPdf,
}: {
  destino: DestinoPdf | null;
  aoAbrirPdf: (d: DestinoPdf) => void;
}) {
  if (!destino) return null;
  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => {
        aoAbrirPdf(destino);
      }}
    >
      <FileText /> Ver no PDF{destino.pagina ? ` (p. ${destino.pagina})` : ""}
    </Button>
  );
}

function Detalhe({ rotulo, children }: { rotulo: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-0.5">
      <dt className="text-xs text-muted-foreground">{rotulo}</dt>
      <dd className="text-sm">{children}</dd>
    </div>
  );
}

function destinoDe(item: { id_documento: string | null; pagina: number | null }): DestinoPdf | null {
  return item.id_documento ? { idDocumento: item.id_documento, pagina: item.pagina } : null;
}

export function CartaoParametro({
  id,
  marca,
  parametro,
  destacado,
  aoAbrirPdf,
}: {
  id: string;
  marca: string;
  parametro: ParametroOut;
  destacado: boolean;
  aoAbrirPdf: (d: DestinoPdf) => void;
}) {
  const faixa =
    parametro.valor_min !== null || parametro.valor_max !== null
      ? `${formatarNumero(parametro.valor_min)} … ${formatarNumero(parametro.valor_max)}${parametro.unidade ? ` ${parametro.unidade}` : ""}`
      : null;
  return (
    <article
      id={id}
      className={cn(
        "space-y-3 rounded-lg border bg-card p-4 transition-shadow",
        destacado && "ring-2 ring-primary",
      )}
    >
      <header className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="font-mono">
          {marca}
        </Badge>
        <CodigoCopiavel codigo={parametro.codigo} className="font-semibold" />
        {parametro.nome && <span className="font-medium">{parametro.nome}</span>}
        {parametro.somente_leitura && (
          <Badge variant="secondary" className="gap-1">
            <Lock className="size-3" /> Somente leitura
          </Badge>
        )}
      </header>
      <p className="text-sm whitespace-pre-line">{parametro.descricao}</p>
      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {faixa && <Detalhe rotulo="Faixa">{faixa}</Detalhe>}
        {parametro.valor_padrao && <Detalhe rotulo="Padrão">{parametro.valor_padrao}</Detalhe>}
        {parametro.unidade && !faixa && <Detalhe rotulo="Unidade">{parametro.unidade}</Detalhe>}
        {parametro.grupo && <Detalhe rotulo="Grupo">{parametro.grupo}</Detalhe>}
        {parametro.versao_firmware && <Detalhe rotulo="Firmware">{parametro.versao_firmware}</Detalhe>}
      </dl>
      <BotaoPdf destino={destinoDe(parametro)} aoAbrirPdf={aoAbrirPdf} />
    </article>
  );
}

export function CartaoFalha({
  id,
  marca,
  falha,
  destacado,
  aoAbrirPdf,
}: {
  id: string;
  marca: string;
  falha: FalhaOut;
  destacado: boolean;
  aoAbrirPdf: (d: DestinoPdf) => void;
}) {
  const ehFalha = falha.tipo === "FALHA";
  return (
    <article
      id={id}
      className={cn(
        "space-y-3 rounded-lg border bg-card p-4 transition-shadow",
        destacado && "ring-2 ring-primary",
      )}
    >
      <header className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="font-mono">
          {marca}
        </Badge>
        <Badge
          variant="outline"
          className={cn(
            "border-transparent",
            ehFalha ? "bg-destructive/15 text-destructive" : "bg-aviso/20 text-foreground",
          )}
        >
          {ROTULO_TIPO_FALHA[falha.tipo]}
        </Badge>
        <CodigoCopiavel codigo={falha.codigo} className="font-semibold" />
        <span className="font-medium">{falha.titulo}</span>
      </header>
      {falha.descricao && <p className="text-sm whitespace-pre-line">{falha.descricao}</p>}
      <dl className="grid gap-3 sm:grid-cols-2">
        {falha.causa && <Detalhe rotulo="Causa">{falha.causa}</Detalhe>}
        {falha.solucao && <Detalhe rotulo="Solução">{falha.solucao}</Detalhe>}
        {falha.reacao && <Detalhe rotulo="Reação">{falha.reacao}</Detalhe>}
        {falha.versao_firmware && <Detalhe rotulo="Firmware">{falha.versao_firmware}</Detalhe>}
      </dl>
      <BotaoPdf destino={destinoDe(falha)} aoAbrirPdf={aoAbrirPdf} />
    </article>
  );
}
