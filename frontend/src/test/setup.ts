import "@testing-library/jest-dom/vitest";

import { cleanup, configure } from "@testing-library/react";
import { afterAll, afterEach, beforeAll } from "vitest";
import { z } from "zod";

import { encerrarSessao } from "@/features/auth/sessao";

import { servidor } from "./servidor";
import { desmontarApps } from "./utils";

z.config(z.locales.ptBR());
// Rotas com code splitting carregam o chunk no primeiro acesso; 1 s (padrão) é pouco no primeiro teste.
configure({ asyncUtilTimeout: 5000 });

// APIs de navegador ausentes no jsdom e usadas por Radix/cmdk/visualizador.
const nada = () => undefined;
globalThis.ResizeObserver = class {
  observe = nada;
  unobserve = nada;
  disconnect = nada;
};
Element.prototype.scrollIntoView = nada;
Element.prototype.hasPointerCapture = () => false;
Element.prototype.releasePointerCapture = () => undefined;
window.matchMedia = (query: string) =>
  ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    addListener: () => undefined,
    removeListener: () => undefined,
    dispatchEvent: () => false,
  }) as MediaQueryList;

beforeAll(() => {
  servidor.listen({ onUnhandledRequest: "error" });
});

afterEach(() => {
  cleanup();
  desmontarApps();
  encerrarSessao("saiu");
  sessionStorage.clear();
  servidor.resetHandlers();
});

afterAll(() => {
  servidor.close();
});
