import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { z } from "zod";

import "./index.css";
import { App } from "./app/providers";

z.config(z.locales.ptBR());

const raiz = document.getElementById("root");
if (!raiz) throw new Error("Elemento #root ausente no index.html");

createRoot(raiz).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
