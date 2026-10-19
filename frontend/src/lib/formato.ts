const numero = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 3 });
const dataHora = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" });

export function formatarNumero(valor: number | null | undefined, unidade?: string | null): string {
  if (valor === null || valor === undefined) return "—";
  return unidade ? `${numero.format(valor)} ${unidade}` : numero.format(valor);
}

export function formatarDataHora(iso: string | null | undefined): string {
  return iso ? dataHora.format(new Date(iso)) : "—";
}

export function formatarBytes(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${numero.format(bytes / 1024)} KiB`;
  return `${numero.format(bytes / (1024 * 1024))} MiB`;
}
