import { describe, expect, it } from "vitest";

import { cn } from "./utils";

describe("cn", () => {
  it("resolve conflitos de classes do Tailwind e ignora valores falsos", () => {
    expect(cn("px-2 text-sm", undefined, null, "px-4")).toBe("text-sm px-4");
  });
});
