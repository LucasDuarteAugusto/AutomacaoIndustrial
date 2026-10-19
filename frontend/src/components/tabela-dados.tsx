import { type ColumnDef, flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

interface TabelaDadosProps<T> {
  // TValue varia por coluna; `any` é o tipo recomendado pelo TanStack Table para listas heterogêneas.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  colunas: ColumnDef<T, any>[];
  dados: T[] | undefined;
  total: number;
  limit: number;
  offset: number;
  aoMudarOffset: (offset: number) => void;
  carregando?: boolean;
  mensagemVazia?: ReactNode;
  aoClicarLinha?: (item: T) => void;
  idLinha: (item: T) => string;
}

/** Tabela com paginação no servidor (`limit`/`offset` → `{ items, total }`). */
export function TabelaDados<T>({
  colunas,
  dados,
  total,
  limit,
  offset,
  aoMudarOffset,
  carregando = false,
  mensagemVazia = "Nenhum registro encontrado.",
  aoClicarLinha,
  idLinha,
}: TabelaDadosProps<T>) {
  // eslint-disable-next-line react-hooks/incompatible-library -- TanStack Table não é memoizável pelo React Compiler (não usado aqui).
  const tabela = useReactTable({
    data: dados ?? [],
    columns: colunas,
    getCoreRowModel: getCoreRowModel(),
    getRowId: idLinha,
    manualPagination: true,
    rowCount: total,
  });

  const inicio = total === 0 ? 0 : offset + 1;
  const fim = Math.min(offset + limit, total);

  return (
    <div className="space-y-3">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {tabela.getHeaderGroups().map((grupo) => (
              <TableRow key={grupo.id}>
                {grupo.headers.map((cabecalho) => (
                  <TableHead key={cabecalho.id}>
                    {cabecalho.isPlaceholder
                      ? null
                      : flexRender(cabecalho.column.columnDef.header, cabecalho.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {carregando && !dados ? (
              Array.from({ length: 5 }, (_, i) => (
                <TableRow key={i}>
                  {colunas.map((_coluna, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-5 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : tabela.getRowModel().rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={colunas.length} className="h-24 text-center text-muted-foreground">
                  {mensagemVazia}
                </TableCell>
              </TableRow>
            ) : (
              tabela.getRowModel().rows.map((linha) => (
                <TableRow
                  key={linha.id}
                  className={cn(aoClicarLinha && "cursor-pointer")}
                  tabIndex={aoClicarLinha ? 0 : undefined}
                  onClick={aoClicarLinha && (() => aoClicarLinha(linha.original))}
                  onKeyDown={
                    aoClicarLinha &&
                    ((evento) => {
                      if (evento.key === "Enter") aoClicarLinha(linha.original);
                    })
                  }
                >
                  {linha.getVisibleCells().map((celula) => (
                    <TableCell key={celula.id}>
                      {flexRender(celula.column.columnDef.cell, celula.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-between gap-2 text-sm text-muted-foreground">
        <span aria-live="polite">
          {inicio}–{fim} de {total}
        </span>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={offset === 0 || carregando}
            onClick={() => {
              aoMudarOffset(Math.max(0, offset - limit));
            }}
          >
            <ChevronLeft /> Anterior
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={offset + limit >= total || carregando}
            onClick={() => {
              aoMudarOffset(offset + limit);
            }}
          >
            Próxima <ChevronRight />
          </Button>
        </div>
      </div>
    </div>
  );
}
