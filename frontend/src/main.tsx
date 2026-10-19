import { createRouter, RouterProvider } from "@tanstack/react-router";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./index.css";
import { routeTree } from "./routeTree.gen";

const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

const raiz = document.getElementById("root");
if (!raiz) throw new Error("Elemento #root ausente no index.html");

createRoot(raiz).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);
