import path from "node:path";

import tailwindcss from "@tailwindcss/vite";
import { tanstackRouter } from "@tanstack/router-plugin/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const API = "http://127.0.0.1:8000";

export default defineConfig(({ mode }) => ({
  plugins: [
    tanstackRouter({
      target: "react",
      // Nos testes, chunks por rota só adicionam espera (e instabilidade) ao primeiro render.
      autoCodeSplitting: mode !== "test",
      routeFileIgnorePattern: "\\.test\\.",
    }),
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: { "@": path.resolve(import.meta.dirname, "src") },
  },
  server: {
    port: 5173,
    proxy: { "/v1": API, "/health": API, "/ready": API },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: false,
    include: ["src/**/*.test.{ts,tsx}"],
  },
}));
