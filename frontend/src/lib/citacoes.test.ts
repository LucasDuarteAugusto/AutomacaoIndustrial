import { describe, expect, it } from "vitest";

import { marcarCitacoes } from "./citacoes";

describe("marcarCitacoes", () => {
  it("transforma [n], [Pn] e [Fn] em links internos", () => {
    expect(marcarCitacoes("Ajuste p1120 [P1] conforme [2]. Falha [F1].")).toBe(
      "Ajuste p1120 [P1](#citacao-P1) conforme [2](#citacao-2). Falha [F1](#citacao-F1).",
    );
  });

  it("separa listas como [1, 3]", () => {
    expect(marcarCitacoes("Veja [1, 3].")).toBe("Veja [1](#citacao-1)[3](#citacao-3).");
  });

  it("não mexe em links Markdown nem em colchetes com texto", () => {
    expect(marcarCitacoes("[manual](https://x.y) e [nota]")).toBe("[manual](https://x.y) e [nota]");
  });
});
