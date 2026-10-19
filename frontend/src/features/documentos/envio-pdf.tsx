import { useQueryClient } from "@tanstack/react-query";
import { FileUp, X } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";

import { mensagemDeErro } from "@/api/problema";
import { enviarPdfDocumento, validarArquivoPdf } from "@/api/upload";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { formatarBytes } from "@/lib/formato";
import { cn } from "@/lib/utils";

import { documentoAtualizado } from "./cache";

interface Envio {
  nome: string;
  tamanho: number;
  percentual: number;
}

export function EnvioPdf({ idDocumento, temArquivo }: { idDocumento: string; temArquivo: boolean }) {
  const queryClient = useQueryClient();
  const entrada = useRef<HTMLInputElement>(null);
  const controlador = useRef<AbortController | null>(null);
  const [envio, setEnvio] = useState<Envio | null>(null);
  const [arrastando, setArrastando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function enviar(arquivo: File) {
    const invalido = validarArquivoPdf(arquivo);
    if (invalido) {
      setErro(invalido);
      return;
    }
    setErro(null);
    setEnvio({ nome: arquivo.name, tamanho: arquivo.size, percentual: 0 });
    const ctrl = new AbortController();
    controlador.current = ctrl;
    try {
      const documento = await enviarPdfDocumento(idDocumento, arquivo, {
        signal: ctrl.signal,
        aoProgredir: (percentual) => {
          setEnvio((atual) => (atual ? { ...atual, percentual } : atual));
        },
      });
      documentoAtualizado(queryClient, documento, { arquivoMudou: true });
      toast.success("PDF enviado. A indexação começou.");
    } catch (falha) {
      if (falha instanceof DOMException && falha.name === "AbortError") toast.info("Envio cancelado.");
      else setErro(mensagemDeErro(falha));
    } finally {
      setEnvio(null);
      controlador.current = null;
      if (entrada.current) entrada.current.value = "";
    }
  }

  if (envio) {
    return (
      <div className="space-y-2 rounded-lg border p-4" role="status" aria-live="polite">
        <div className="flex items-center gap-2 text-sm">
          <FileUp className="size-4" aria-hidden />
          <span className="min-w-0 flex-1 truncate">{envio.nome}</span>
          <span className="text-muted-foreground tabular-nums">
            {envio.percentual}% de {formatarBytes(envio.tamanho)}
          </span>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Cancelar envio"
            onClick={() => controlador.current?.abort()}
          >
            <X />
          </Button>
        </div>
        <Progress value={envio.percentual} aria-label="Progresso do envio" />
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div
        className={cn(
          "flex flex-col items-center gap-2 rounded-lg border-2 border-dashed p-6 text-center text-sm transition-colors",
          arrastando && "border-primary bg-primary/5",
        )}
        onDragOver={(e) => {
          e.preventDefault();
          setArrastando(true);
        }}
        onDragLeave={() => {
          setArrastando(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          setArrastando(false);
          const arquivo = e.dataTransfer.files[0];
          if (arquivo) void enviar(arquivo);
        }}
      >
        <FileUp className="size-8 text-muted-foreground" aria-hidden />
        <p>
          Arraste o PDF aqui ou{" "}
          <Button variant="link" className="h-auto p-0" onClick={() => entrada.current?.click()}>
            escolha um arquivo
          </Button>
        </p>
        <p className="text-xs text-muted-foreground">
          PDF até 50 MiB.{temArquivo && " Enviar outro arquivo substitui o atual e refaz a indexação."}
        </p>
        <input
          ref={entrada}
          type="file"
          accept="application/pdf,.pdf"
          className="sr-only"
          aria-label="Arquivo PDF"
          onChange={(e) => {
            const arquivo = e.target.files?.[0];
            if (arquivo) void enviar(arquivo);
          }}
        />
      </div>
      {erro && (
        <p role="alert" className="text-sm text-destructive">
          {erro}
        </p>
      )}
    </div>
  );
}
