import { zodResolver } from "@hookform/resolvers/zod";
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import type { z } from "zod";

import { useBootstrap } from "@/api/gerado/auth/auth";
import { BootstrapBody } from "@/api/gerado/zod/auth/auth";
import { aplicarErrosNoFormulario, ehProblema, mensagemDeErro } from "@/api/problema";
import { AlertaFormulario } from "@/components/alerta-formulario";
import { Campo } from "@/components/campo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { LayoutAutenticacao } from "@/features/auth/layout-autenticacao";
import { iniciarSessao, obterSessao } from "@/features/auth/sessao";

const esquema = BootstrapBody.extend({ confirmacao: BootstrapBody.shape.senha }).refine(
  (dados) => dados.senha === dados.confirmacao,
  { path: ["confirmacao"], message: "As senhas não conferem." },
);
type DadosPrimeiroAcesso = z.infer<typeof esquema>;

export const Route = createFileRoute("/primeiro-acesso")({
  beforeLoad: () => {
    if (obterSessao()) throw redirect({ to: "/assistente" });
  },
  component: PaginaPrimeiroAcesso,
});

function PaginaPrimeiroAcesso() {
  const navigate = useNavigate();
  const bootstrap = useBootstrap();
  const form = useForm<DadosPrimeiroAcesso>({
    resolver: zodResolver(esquema),
    defaultValues: { nome: "", email: "", senha: "", confirmacao: "" },
  });
  const { errors, isSubmitting } = form.formState;

  const enviar = form.handleSubmit(async ({ confirmacao: _confirmacao, ...dados }) => {
    try {
      iniciarSessao(await bootstrap.mutateAsync({ data: dados }));
      toast.success("Administrador criado. Bem-vindo!");
      await navigate({ to: "/assistente" });
    } catch (erro) {
      if (ehProblema(erro, 409)) {
        toast.info("O sistema já foi configurado. Entre com sua conta.");
        await navigate({ to: "/login" });
      } else if (!aplicarErrosNoFormulario(erro, form.setError, ["nome", "email", "senha"])) {
        form.setError("root", { message: mensagemDeErro(erro) });
      }
    }
  });

  return (
    <LayoutAutenticacao
      titulo="Primeiro acesso"
      descricao="Crie a conta de administrador. Ela poderá cadastrar os demais usuários."
    >
      <form onSubmit={enviar} className="grid gap-4" noValidate>
        <AlertaFormulario mensagem={errors.root?.message} />
        <Campo id="nome" rotulo="Nome" erro={errors.nome?.message}>
          <Input autoComplete="name" autoFocus {...form.register("nome")} />
        </Campo>
        <Campo id="email" rotulo="E-mail" erro={errors.email?.message}>
          <Input type="email" autoComplete="username" {...form.register("email")} />
        </Campo>
        <Campo id="senha" rotulo="Senha" erro={errors.senha?.message} dica="Mínimo de 8 caracteres.">
          <Input type="password" autoComplete="new-password" {...form.register("senha")} />
        </Campo>
        <Campo id="confirmacao" rotulo="Confirmar senha" erro={errors.confirmacao?.message}>
          <Input type="password" autoComplete="new-password" {...form.register("confirmacao")} />
        </Campo>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting && <Loader2 className="animate-spin" />}
          Criar administrador
        </Button>
      </form>
    </LayoutAutenticacao>
  );
}
