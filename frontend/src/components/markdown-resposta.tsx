import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

import { marcarCitacoes, PREFIXO_CITACAO as PREFIXO } from "@/lib/citacoes";
import { cn } from "@/lib/utils";

interface MarkdownRespostaProps {
  texto: string;
  /** Recebe "1", "P2", "F1"… */
  aoClicarMarca: (marca: string) => void;
  marcasValidas: ReadonlySet<string>;
  className?: string;
}

export function MarkdownResposta({ texto, aoClicarMarca, marcasValidas, className }: MarkdownRespostaProps) {
  const componentes: Components = {
    a: ({ href, children }) => {
      if (href?.startsWith(PREFIXO)) {
        const marca = href.slice(PREFIXO.length);
        if (!marcasValidas.has(marca)) return <span className="text-muted-foreground">[{marca}]</span>;
        return (
          <button
            type="button"
            onClick={() => {
              aoClicarMarca(marca);
            }}
            className="mx-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded bg-primary/10 px-1 align-text-top font-mono text-[0.7rem] font-semibold text-primary hover:bg-primary/20"
            aria-label={`Ver fonte ${marca}`}
          >
            {marca}
          </button>
        );
      }
      return (
        <a href={href} target="_blank" rel="noreferrer" className="text-primary underline underline-offset-4">
          {children}
        </a>
      );
    },
  };

  return (
    <div
      className={cn(
        "space-y-3 leading-relaxed",
        "[&_ol]:list-decimal [&_ol]:space-y-1 [&_ol]:pl-6 [&_ul]:list-disc [&_ul]:space-y-1 [&_ul]:pl-6",
        "[&_h1]:text-lg [&_h1]:font-semibold [&_h2]:font-semibold [&_h3]:font-semibold [&_strong]:font-semibold",
        "[&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_code]:font-mono [&_code]:text-[0.9em]",
        "[&_pre]:overflow-x-auto [&_pre]:rounded-md [&_pre]:bg-muted [&_pre]:p-3",
        "[&_table]:w-full [&_table]:text-sm [&_td]:border [&_td]:px-2 [&_td]:py-1 [&_th]:border [&_th]:px-2 [&_th]:py-1 [&_th]:text-left",
        className,
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={componentes}>
        {marcarCitacoes(texto)}
      </ReactMarkdown>
    </div>
  );
}
