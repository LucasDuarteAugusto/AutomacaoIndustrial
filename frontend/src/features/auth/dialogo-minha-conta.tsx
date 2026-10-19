import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import type { z } from "zod";

import { useTrocarSenha } from "@/api/gerado/auth/auth";
import { TrocarSenhaBody } from "@/api/gerado/zod/auth/auth";
import { aplicarErrosNoFormulario, ehProblema, mensagemDeErro } from "@/api/problema";
import { AlertaFormulario } from "@/components/alerta-formulario";
import { Campo } from "@/components/campo";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ROTULO_PERFIL } from "@/lib/rotulos";

import { useSessao } from "./sessao";

const esquema = TrocarSenhaBody.extend({ confirmacao: TrocarSenhaBody.shape.senha_nova }).refine(
  (dados) => dados.senha_nova === dados.confirmacao,
  { path: ["confirmacao"], message: "As senhas não conferem." },
);
type DadosTrocaSenha = z.infer<typeof esquema>;

const VAZIO: DadosTrocaSenha = { senha_atual: "", senha_nova: "", confirmacao: "" };

export function DialogoMinhaConta({
  aberto,
  aoMudar,
}: {
  aberto: boolean;
  aoMudar: (aberto: boolean) => void;
}) {
  const usuario = useSessao()?.usuario;
  const trocarSenha = useTrocarSenha();
  const form = useForm<DadosTrocaSenha>({ resolver: zodResolver(esquema), defaultValues: VAZIO });
  const { errors, isSubmitting } = form.formState;

  const enviar = form.handleSubmit(async ({ confirmacao: _confirmacao, ...dados }) => {
    try {
      await trocarSenha.mutateAsync({ data: dados });
      toast.success("Senha alterada.");
      form.reset(VAZIO);
      aoMudar(false);
    } catch (erro) {
      if (aplicarErrosNoFormulario(erro, form.setError, ["senha_atual", "senha_nova"])) return;
      if (ehProblema(erro, 422)) {
        const campo = erro.detalhe?.toLowerCase().includes("atual") ? "senha_atual" : "senha_nova";
        form.setError(campo, { message: erro.detalhe ?? erro.titulo });
        return;
      }
      form.setError("root", { message: mensagemDeErro(erro) });
    }
  });

  return (
    <Dialog
      open={aberto}
      onOpenChange={(valor) => {
        if (!valor) form.reset(VAZIO);
        aoMudar(valor);
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Minha conta</DialogTitle>
          <DialogDescription>
            {usuario?.nome} · {usuario?.email}{" "}
            {usuario && <Badge variant="secondary">{ROTULO_PERFIL[usuario.perfil]}</Badge>}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={enviar} className="grid gap-4" noValidate>
          <AlertaFormulario mensagem={errors.root?.message} />
          <Campo id="senha_atual" rotulo="Senha atual" erro={errors.senha_atual?.message}>
            <Input type="password" autoComplete="current-password" {...form.register("senha_atual")} />
          </Campo>
          <Campo
            id="senha_nova"
            rotulo="Nova senha"
            erro={errors.senha_nova?.message}
            dica="Mínimo de 8 caracteres."
          >
            <Input type="password" autoComplete="new-password" {...form.register("senha_nova")} />
          </Campo>
          <Campo id="confirmacao" rotulo="Confirmar nova senha" erro={errors.confirmacao?.message}>
            <Input type="password" autoComplete="new-password" {...form.register("confirmacao")} />
          </Campo>
          <DialogFooter>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="animate-spin" />}
              Alterar senha
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
