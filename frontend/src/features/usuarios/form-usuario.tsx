import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { useAlterarUsuario, useCriarUsuario } from "@/api/gerado/auth/auth";
import { Perfil, type UsuarioOut } from "@/api/gerado/modelos";
import {
  CriarUsuarioBody,
  criarUsuarioBodyNomeMax,
  criarUsuarioBodySenhaMax,
  criarUsuarioBodySenhaMin,
} from "@/api/gerado/zod/auth/auth";
import { aplicarErrosNoFormulario, mensagemDeErro } from "@/api/problema";
import { AlertaFormulario } from "@/components/alerta-formulario";
import { Campo } from "@/components/campo";
import { CampoAtivo } from "@/components/campo-ativo";
import { SelectOpcoes } from "@/components/select-opcoes";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { PERFIS, ROTULO_PERFIL } from "@/lib/rotulos";

const esquema = z.object({
  email: CriarUsuarioBody.shape.email,
  nome: CriarUsuarioBody.shape.nome.trim(),
  senha: z.string().max(criarUsuarioBodySenhaMax),
  perfil: z.enum(Perfil),
  ativo: z.boolean(),
});
type Dados = z.infer<typeof esquema>;

const VAZIO: Dados = { email: "", nome: "", senha: "", perfil: "OPERADOR", ativo: true };

const CAMPOS = ["email", "nome", "senha", "perfil", "ativo"] as const;

export function FormUsuario({
  aberto,
  aoMudar,
  usuario,
  aoSalvar,
}: {
  aberto: boolean;
  aoMudar: (aberto: boolean) => void;
  usuario: UsuarioOut | null;
  aoSalvar: () => void;
}) {
  const criar = useCriarUsuario();
  const alterar = useAlterarUsuario();
  const editando = usuario !== null;

  const form = useForm<Dados>({
    resolver: zodResolver(esquema),
    defaultValues: VAZIO,
  });
  const { errors, isSubmitting } = form.formState;

  useEffect(() => {
    if (!aberto) return;
    form.reset(
      usuario
        ? {
            email: usuario.email,
            nome: usuario.nome,
            senha: "",
            perfil: usuario.perfil,
            ativo: usuario.ativo,
          }
        : VAZIO,
    );
  }, [aberto, usuario, form]);

  const enviar = form.handleSubmit(async (dados) => {
    if (!editando && dados.senha.length < criarUsuarioBodySenhaMin) {
      form.setError("senha", {
        type: "manual",
        message: `A senha precisa ter ao menos ${criarUsuarioBodySenhaMin} caracteres.`,
      });
      return;
    }
    if (editando && dados.senha !== "" && dados.senha.length < criarUsuarioBodySenhaMin) {
      form.setError("senha", {
        type: "manual",
        message: `A senha precisa ter ao menos ${criarUsuarioBodySenhaMin} caracteres.`,
      });
      return;
    }
    try {
      if (editando) {
        await alterar.mutateAsync({
          idUsuario: usuario.id_usuario,
          data: {
            nome: dados.nome,
            senha: dados.senha || null,
            perfil: dados.perfil,
            ativo: dados.ativo,
          },
        });
        toast.success("Usuário atualizado.");
      } else {
        await criar.mutateAsync({
          data: {
            email: dados.email,
            senha: dados.senha,
            nome: dados.nome,
            perfil: dados.perfil,
            ativo: dados.ativo,
          },
        });
        toast.success("Usuário cadastrado.");
      }
      aoSalvar();
      aoMudar(false);
    } catch (erro) {
      if (!aplicarErrosNoFormulario(erro, form.setError, CAMPOS)) {
        form.setError("root", { message: mensagemDeErro(erro) });
      }
    }
  });

  return (
    <Sheet
      open={aberto}
      onOpenChange={(valor) => {
        if (!isSubmitting) aoMudar(valor);
      }}
    >
      <SheetContent className="flex w-full flex-col gap-0 sm:max-w-md">
        <SheetHeader className="border-b">
          <SheetTitle>{editando ? "Editar usuário" : "Novo usuário"}</SheetTitle>
          <SheetDescription>
            {editando
              ? "Deixe a senha em branco para manter a atual."
              : `Senha com ao menos ${criarUsuarioBodySenhaMin} caracteres.`}
          </SheetDescription>
        </SheetHeader>
        <form onSubmit={enviar} className="flex min-h-0 flex-1 flex-col" noValidate>
          <div className="grid flex-1 gap-4 overflow-y-auto p-4">
            <AlertaFormulario mensagem={errors.root?.message} />
            <Campo id="usu-email" rotulo="E-mail" erro={errors.email?.message}>
              <Input
                type="email"
                placeholder="tecnico@example.com"
                autoComplete="off"
                disabled={editando}
                {...form.register("email")}
              />
            </Campo>
            <Campo
              id="usu-nome"
              rotulo="Nome"
              erro={errors.nome?.message}
              dica={`Até ${criarUsuarioBodyNomeMax} caracteres.`}
            >
              <Input placeholder="Técnica de Campo" {...form.register("nome")} />
            </Campo>
            <Campo
              id="usu-senha"
              rotulo={editando ? "Nova senha" : "Senha"}
              erro={errors.senha?.message}
              dica={editando ? "Opcional." : undefined}
            >
              <Input type="password" autoComplete="new-password" {...form.register("senha")} />
            </Campo>
            <div className="grid gap-1.5">
              <span className="text-sm font-medium">Perfil</span>
              <Controller
                control={form.control}
                name="perfil"
                render={({ field }) => (
                  <SelectOpcoes
                    valor={field.value}
                    aoMudar={(valor) => {
                      if (valor) field.onChange(valor);
                    }}
                    opcoes={PERFIS}
                    rotulos={ROTULO_PERFIL}
                  />
                )}
              />
            </div>
            <CampoAtivo control={form.control} erro={errors.ativo?.message} />
          </div>
          <SheetFooter className="border-t">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="animate-spin" />}
              {editando ? "Salvar" : "Cadastrar"}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
}
