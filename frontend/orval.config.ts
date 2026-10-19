import { defineConfig } from "orval";

export default defineConfig({
  api: {
    input: "./openapi.json",
    output: {
      target: "src/api/gerado/endpoints.ts",
      schemas: "src/api/gerado/modelos",
      client: "react-query",
      httpClient: "fetch",
      mode: "tags-split",
      mock: { generators: [{ type: "msw" }], indexMockFiles: true },
      clean: true,
      override: {
        mutator: { path: "src/api/http.ts", name: "http" },
        fetch: { includeHttpResponseReturnType: false },
        query: { signal: true },
      },
    },
  },
  zod: {
    input: "./openapi.json",
    output: {
      target: "src/api/gerado/zod/esquemas.ts",
      client: "zod",
      mode: "tags-split",
    },
  },
});
