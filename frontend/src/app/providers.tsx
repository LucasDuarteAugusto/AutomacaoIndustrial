import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "@tanstack/react-router";
import { useState } from "react";
import { Toaster } from "sonner";

import { TooltipProvider } from "@/components/ui/tooltip";
import { useTema } from "@/lib/tema";

import { criarQueryClient } from "./query-client";
import { criarRouter } from "./router";

export function App() {
  const [queryClient] = useState(criarQueryClient);
  const [{ router }] = useState(() => criarRouter(queryClient));
  const [tema] = useTema();

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider delayDuration={300}>
        <RouterProvider router={router} />
        <Toaster theme={tema === "escuro" ? "dark" : "light"} richColors closeButton position="top-right" />
      </TooltipProvider>
    </QueryClientProvider>
  );
}
