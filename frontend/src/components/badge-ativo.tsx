import { Badge } from "@/components/ui/badge";

export function BadgeAtivo({ ativo }: { ativo: boolean }) {
  return (
    <Badge variant={ativo ? "secondary" : "outline"}>{ativo ? "Ativo" : "Inativo"}</Badge>
  );
}
