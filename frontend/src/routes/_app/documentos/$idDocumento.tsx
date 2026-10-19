import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { ArrowLeft, CircleAlert, Eye, Loader2, RefreshCw, Trash2 } from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { toast } from "sonner";

import {
  getObterDocumentoQueryOptions,
  useExcluirDocumento,
  useReprocessarDocumento,
} from "@/api/gerado/documentos/documentos";
import type { StatusProcessamento } from "@/api/gerado/modelos";
import { ehProblema, mensagemDeErro } from "@/api/problema";
import { CabecalhoPagina } from "@/components/cabecalho-pagina";
import { CodigoCopiavel } from "@/components/codigo-copiavel";
import { ConfirmarExclusao } from "@/components/confirmar-exclusao";
import { ProblemaAlerta } from "@/components/problema-alerta";
import { StatusBadge } from "@/components/status-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { type PdfAberto, VisualizadorPdf } from "@/components/visualizador-pdf";
import { usePodeEscrever } from "@/features/auth/sessao";
import { documentoAtualizado, documentoRemovido, estaProcessando } from "@/features/documentos/cache";
import { EnvioPdf } from "@/features/documentos/envio-pdf";
import { formatarBytes, formatarDataHora } from "@/lib/formato";
import { ROTULO_IDIOMA, ROTULO_TIPO_DOCUMENTO } from "@/lib/rotulos";

export const Route = createFileRoute("/_app/documentos/$idDocumento")({
  component: PaginaDocumento,
});

function Item({ rotulo, children }: { rotulo: string; children: ReactNode }) {
  return (
    <div className="grid gap-0.5">
      <dt className="text-xs text-muted-foreground">{rotulo}</dt>
      <dd className="text-sm">{children}</dd>
    </div>
  );
}

/** Avisa quando a indexação termina enquanto o usuário está na página. */
function useAvisoFimIndexacao(status: StatusProcessamento | undefined) {
  const anterior = useRef(status);
  useEffect(() => {
    const antes = anterior.current;
    anterior.current = status;
    if (antes !== "PROCESSANDO" && antes !== "PENDENTE") return;
    if (status === "INDEXADO") toast.success("Indexação concluída. O documento já aparece na busca.");
    if (status === "ERRO") toast.error("A indexação falhou. Veja o erro na página.");
  }, [status]);
}

function PaginaDocumento() {
  const { idDocumento } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const podeEscrever = usePodeEscrever();
  const [excluindo, setExcluindo] = useState(false);
  const [pdf, setPdf] = useState<PdfAberto | null>(null);

  const consulta = useQuery({
    ...getObterDocumentoQueryOptions(idDocumento),
    refetchInterval: (q) => (q.state.data && estaProcessando(q.state.data) ? 3000 : false),
  });
  const reprocessar = useReprocessarDocumento();
  const excluir = useExcluirDocumento();
  useAvisoFimIndexacao(consulta.data?.status_processamento);

  const voltar = (
    <Button variant="ghost" size="sm" asChild>
      <Link to="/documentos">
        <ArrowLeft /> Documentos
      </Link>
    </Button>
  );

  if (consulta.isPending) {
    return (
      <div className="space-y-4">
        {voltar}
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (consulta.isError) {
    return (
      <div className="space-y-4">
        {voltar}
        {ehProblema(consulta.error, 404) ? (
          <p className="text-muted-foreground">Documento não encontrado. Ele pode ter sido excluído.</p>
        ) : (
          <ProblemaAlerta erro={consulta.error} aoTentarDeNovo={() => void consulta.refetch()} />
        )}
      </div>
    );
  }

  const documento = consulta.data;
  const processando = estaProcessando(documento);

  async function aoReprocessar() {
    try {
      const atualizado = await reprocessar.mutateAsync({ idDocumento });
      documentoAtualizado(queryClient, atualizado);
      toast.success("Reprocessamento iniciado.");
    } catch (erro) {
      toast.error(mensagemDeErro(erro));
    }
  }

  async function aoExcluir() {
    try {
      await excluir.mutateAsync({ idDocumento });
    } catch (erro) {
      toast.error(mensagemDeErro(erro));
      throw erro;
    }
    documentoRemovido(queryClient, idDocumento);
    toast.success("Documento excluído.");
    await navigate({ to: "/documentos" });
  }

  return (
    <div className="space-y-4">
      {voltar}
      <CabecalhoPagina
        titulo={documento.titulo}
        descricao={
          <span className="flex flex-wrap items-center gap-2">
            <StatusBadge status={documento.status_processamento} />
            {documento.codigo_documento && <CodigoCopiavel codigo={documento.codigo_documento} />}
          </span>
        }
        acoes={
          <>
            {documento.chave_arquivo && (
              <Button
                variant="outline"
                onClick={() => {
                  setPdf({ idDocumento, titulo: documento.titulo });
                }}
              >
                <Eye /> Visualizar PDF
              </Button>
            )}
            {podeEscrever && documento.chave_arquivo && (
              <Button
                variant="outline"
                disabled={documento.status_processamento === "PROCESSANDO" || reprocessar.isPending}
                onClick={() => void aoReprocessar()}
              >
                {reprocessar.isPending ? <Loader2 className="animate-spin" /> : <RefreshCw />} Reprocessar
              </Button>
            )}
            {podeEscrever && (
              <Button
                variant="outline"
                className="text-destructive"
                onClick={() => {
                  setExcluindo(true);
                }}
              >
                <Trash2 /> Excluir
              </Button>
            )}
          </>
        }
      />

      {documento.status_processamento === "ERRO" && (
        <Alert variant="destructive">
          <CircleAlert />
          <AlertTitle>A indexação falhou</AlertTitle>
          <AlertDescription>
            {documento.erro_processamento ?? "Erro sem detalhes."}
            {podeEscrever && " Corrija a causa (ex.: chave da Voyage) e use Reprocessar."}
          </AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Metadados</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 sm:grid-cols-2">
              <Item rotulo="Tipo">{ROTULO_TIPO_DOCUMENTO[documento.tipo_documento]}</Item>
              <Item rotulo="Idioma">{ROTULO_IDIOMA[documento.idioma]}</Item>
              <Item rotulo="Edição">{documento.edicao ?? "—"}</Item>
              <Item rotulo="Firmware">{documento.versao_firmware ?? "—"}</Item>
              <Item rotulo="Famílias">
                <span className="flex flex-wrap gap-1">
                  {documento.familias.map((f) => (
                    <Badge key={f.id_familia} variant="secondary">
                      {f.nome}
                    </Badge>
                  ))}
                </span>
              </Item>
              <Item rotulo="Equipamentos">
                {documento.equipamentos.length === 0 ? (
                  "Todos da família"
                ) : (
                  <span className="flex flex-wrap gap-1">
                    {documento.equipamentos.map((e) => (
                      <Badge key={e.id_equipamento} variant="outline" className="font-mono" title={e.nome}>
                        {e.codigo_pedido}
                      </Badge>
                    ))}
                  </span>
                )}
              </Item>
              <Item rotulo="Criado em">{formatarDataHora(documento.created_at)}</Item>
              <Item rotulo="Atualizado em">{formatarDataHora(documento.updated_at)}</Item>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Arquivo</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {documento.chave_arquivo ? (
              <dl className="grid gap-4 sm:grid-cols-3">
                <Item rotulo="Tamanho">{formatarBytes(documento.tamanho_bytes)}</Item>
                <Item rotulo="Páginas">{documento.paginas ?? (processando ? "Calculando…" : "—")}</Item>
                <Item rotulo="SHA-256">
                  {documento.hash_sha256 ? (
                    <span title={documento.hash_sha256} className="font-mono text-xs">
                      {documento.hash_sha256.slice(0, 12)}…
                    </span>
                  ) : (
                    "—"
                  )}
                </Item>
              </dl>
            ) : (
              <p className="text-sm text-muted-foreground">Nenhum PDF enviado ainda.</p>
            )}
            {processando && (
              <p className="flex items-center gap-2 text-sm text-muted-foreground" role="status">
                <Loader2 className="size-4 animate-spin" /> Indexando o PDF… esta página atualiza sozinha.
              </p>
            )}
            {podeEscrever && !processando && (
              <EnvioPdf idDocumento={idDocumento} temArquivo={documento.chave_arquivo !== null} />
            )}
          </CardContent>
        </Card>
      </div>

      <ConfirmarExclusao
        aberto={excluindo}
        aoMudar={setExcluindo}
        titulo="Excluir documento?"
        descricao={
          <>
            <strong>{documento.titulo}</strong> será removido junto com o PDF e os trechos indexados. Esta
            ação não pode ser desfeita.
          </>
        }
        aoConfirmar={aoExcluir}
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
