import { http as rota, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import { problema, servidor } from "@/test/servidor";

import { http } from "./http";
import { aplicarErrosNoFormulario, ehProblema, mensagemDeErro, ProblemaApi } from "./problema";
import { configurarSessaoHttp } from "./sessao-http";

async function capturarErro(promessa: Promise<unknown>): Promise<ProblemaApi> {
  try {
    await promessa;
  } catch (erro) {
    if (erro instanceof ProblemaApi) return erro;
    throw erro;
  }
  throw new Error("esperava erro");
}

describe("http", () => {
  it("envia o Bearer da sessão e devolve o JSON", async () => {
    configurarSessaoHttp({ obterToken: () => "abc", aoNaoAutorizado: vi.fn() });
    let autorizacao: string | null = null;
    servidor.use(
      rota.get("*/v1/teste", ({ request }) => {
        autorizacao = request.headers.get("Authorization");
        return HttpResponse.json({ ok: true });
      }),
    );

    await expect(http("/v1/teste")).resolves.toEqual({ ok: true });
    expect(autorizacao).toBe("Bearer abc");
  });

  it("204 devolve undefined", async () => {
    servidor.use(rota.delete("*/v1/teste", () => new HttpResponse(null, { status: 204 })));
    await expect(http("/v1/teste", { method: "DELETE" })).resolves.toBeUndefined();
  });

  it("401 com token avisa a sessão", async () => {
    const aoNaoAutorizado = vi.fn();
    configurarSessaoHttp({ obterToken: () => "expirado", aoNaoAutorizado });
    servidor.use(
      rota.get("*/v1/teste", () => problema(401, "Não autorizado", "Token inválido ou expirado.")),
    );

    const erro = await capturarErro(http("/v1/teste"));
    expect(erro.status).toBe(401);
    expect(aoNaoAutorizado).toHaveBeenCalledOnce();
  });

  it("401 sem token (login errado) não encerra sessão", async () => {
    const aoNaoAutorizado = vi.fn();
    configurarSessaoHttp({ obterToken: () => null, aoNaoAutorizado });
    servidor.use(
      rota.post("*/v1/auth/login", () => problema(401, "Não autorizado", "E-mail ou senha inválidos.")),
    );

    await capturarErro(http("/v1/auth/login", { method: "POST" }));
    expect(aoNaoAutorizado).not.toHaveBeenCalled();
  });

  it("422 traz os erros por campo e 409 o detalhe", async () => {
    servidor.use(
      rota.post("*/v1/teste", () =>
        problema(422, "Dados de entrada inválidos", "Um ou mais campos não passaram na validação.", {
          errors: [{ loc: ["body", "titulo"], msg: "Campo obrigatório", type: "missing" }],
        }),
      ),
      rota.put("*/v1/teste", () => problema(409, "Conflito", "Já existe um documento com este arquivo.")),
    );

    const erro422 = await capturarErro(http("/v1/teste", { method: "POST" }));
    expect(erro422.erros).toEqual([{ loc: ["body", "titulo"], msg: "Campo obrigatório", type: "missing" }]);

    const erro409 = await capturarErro(http("/v1/teste", { method: "PUT" }));
    expect(mensagemDeErro(erro409)).toBe("Já existe um documento com este arquivo.");
  });

  it("429 lê o Retry-After e 403 tem mensagem de perfil", async () => {
    servidor.use(
      rota.post("*/v1/agente/perguntar", () =>
        HttpResponse.json(
          {
            title: "Limite de requisições excedido",
            status: 429,
            detail: "Limite de 20 requisições por 60s.",
          },
          { status: 429, headers: { "Retry-After": "17" } },
        ),
      ),
      rota.post("*/v1/documentos", () => problema(403, "Proibido", "Perfil LEITURA não pode alterar dados.")),
    );

    const erro429 = await capturarErro(http("/v1/agente/perguntar", { method: "POST" }));
    expect(ehProblema(erro429, 429)).toBe(true);
    expect(erro429.retryAfter).toBe(17);
    expect(mensagemDeErro(erro429)).toBe("Muitas requisições. Tente novamente em 17 s.");

    const erro403 = await capturarErro(http("/v1/documentos", { method: "POST" }));
    expect(mensagemDeErro(erro403)).toBe("Seu perfil não permite esta ação.");
  });

  it("falha de rede vira status 0", async () => {
    servidor.use(rota.get("*/v1/teste", () => HttpResponse.error()));
    const erro = await capturarErro(http("/v1/teste"));
    expect(erro.status).toBe(0);
    expect(mensagemDeErro(erro)).toBe("Não foi possível falar com o servidor.");
  });
});

describe("aplicarErrosNoFormulario", () => {
  it("leva erros 422 do corpo para os campos conhecidos", () => {
    const setError = vi.fn();
    const erro = new ProblemaApi({
      status: 422,
      titulo: "Dados de entrada inválidos",
      erros: [
        { loc: ["body", "email"], msg: "e-mail inválido", type: "value_error" },
        { loc: ["query", "limit"], msg: "ignorado", type: "x" },
      ],
    });

    expect(aplicarErrosNoFormulario(erro, setError, ["email", "senha"])).toBe(true);
    expect(setError).toHaveBeenCalledExactlyOnceWith("email", {
      type: "servidor",
      message: "e-mail inválido",
    });
  });

  it("não aplica nada para outros status", () => {
    const setError = vi.fn();
    expect(
      aplicarErrosNoFormulario(new ProblemaApi({ status: 409, titulo: "Conflito" }), setError, ["email"]),
    ).toBe(false);
    expect(setError).not.toHaveBeenCalled();
  });
});
