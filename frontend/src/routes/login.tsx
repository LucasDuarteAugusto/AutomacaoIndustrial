import { zodResolver } from "@hookform/resolvers/zod";
import { createFileRoute, Navigate, redirect, useRouter } from "@tanstack/react-router";
import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { useLogin, useStatusBootstrap } from "@/api/gerado/auth/auth";
import type { LoginRequest } from "@/api/gerado/modelos";
import { LoginBody } from "@/api/gerado/zod/auth/auth";
import { aplicarErrosNoFormulario, ehProblema, mensagemDeErro } from "@/api/problema";
import { AlertaFormulario } from "@/components/alerta-formulario";
import { Campo } from "@/components/campo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { LayoutAutenticacao } from "@/features/auth/layout-autenticacao";
import { destinoSeguro, iniciarSessao, obterSessao } from "@/features/auth/sessao";

export const Route = createFileRoute("/login")({
  validateSearch: z.object({ redirect: z.string().optional() }),
  beforeLoad: ({ search }) => {
    if (obterSessao()) throw redirect({ href: destinoSeguro(search.redirect) });
  },
  component: PaginaLogin,
});

function PaginaLogin() {
  const { redirect: destino } = Route.useSearch();
  const router = useRouter();
  const statusBootstrap = useStatusBootstrap();
  const login = useLogin();
  const form = useForm<LoginRequest>({
    resolver: zodResolver(LoginBody),
    defaultValues: { email: "", senha: "" },
  });
  const { errors, isSubmitting } = form.formState;

  if (statusBootstrap.data?.necessario) return <Navigate to="/primeiro-acesso" />;

  const enviar = form.handleSubmit(async (dados) => {
    try {
      iniciarSessao(await login.mutateAsync({ data: dados }));
      await router.navigate({ href: destinoSeguro(destino) });
    } catch (erro) {
      if (ehProblema(erro, 401)) form.setError("root", { message: "E-mail ou senha inválidos." });
      else if (ehProblema(erro, 403))
        form.setError("root", { message: "Usuário inativo. Fale com o administrador." });
      else if (!aplicarErrosNoFormulario(erro, form.setError, ["email", "senha"]))
        form.setError("root", { message: mensagemDeErro(erro) });
    }
  });

  return (
    <LayoutAutenticacao titulo="Entrar" descricao="Use seu e-mail e senha cadastrados.">
      <form onSubmit={enviar} className="grid gap-4" noValidate>
        <AlertaFormulario mensagem={errors.root?.message} />
        <Campo id="email" rotulo="E-mail" erro={errors.email?.message}>
          <Input type="email" autoComplete="username" autoFocus {...form.register("email")} />
        </Campo>
        <Campo id="senha" rotulo="Senha" erro={errors.senha?.message}>
          <Input type="password" autoComplete="current-password" {...form.register("senha")} />
        </Campo>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting && <Loader2 className="animate-spin" />}
          Entrar
        </Button>
      </form>
    </LayoutAutenticacao>
  );
}
