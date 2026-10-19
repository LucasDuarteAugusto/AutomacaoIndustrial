import type { DocumentoOut, Perfil, TokenOut, UsuarioOut } from "@/api/gerado/modelos";
import { iniciarSessao } from "@/features/auth/sessao";

export function usuario(perfil: Perfil = "ADMIN"): UsuarioOut {
  return {
    id_usuario: "00000000-0000-4000-8000-000000000001",
    email: "tecnico@example.com",
    nome: "Técnica de Campo",
    perfil,
    ativo: true,
    created_at: "2026-10-01T12:00:00Z",
    updated_at: "2026-10-01T12:00:00Z",
  };
}

export function token(perfil: Perfil = "ADMIN"): TokenOut {
  return {
    access_token: "token-de-teste",
    token_type: "bearer",
    expires_in: 28_800,
    usuario: usuario(perfil),
  };
}

export function entrarComo(perfil: Perfil = "ADMIN") {
  return iniciarSessao(token(perfil));
}

export const ID_DOCUMENTO = "11111111-1111-4111-8111-111111111111";

export function documento(parcial: Partial<DocumentoOut> = {}): DocumentoOut {
  return {
    id_documento: ID_DOCUMENTO,
    titulo: "SINAMICS G120 - Lista de parâmetros",
    tipo_documento: "LISTA_PARAMETROS",
    idioma: "pt-BR",
    codigo_documento: "A5E33840768",
    edicao: "09/2023",
    versao_firmware: "4.7 SP14",
    chave_arquivo: `${ID_DOCUMENTO}/abc.pdf`,
    hash_sha256: "a".repeat(64),
    tamanho_bytes: 2048,
    paginas: 12,
    status_processamento: "INDEXADO",
    erro_processamento: null,
    familias: [{ id_familia: "22222222-2222-4222-8222-222222222222", nome: "SINAMICS G120" }],
    equipamentos: [],
    created_at: "2026-10-10T12:00:00Z",
    updated_at: "2026-10-11T12:00:00Z",
    ...parcial,
  };
}
