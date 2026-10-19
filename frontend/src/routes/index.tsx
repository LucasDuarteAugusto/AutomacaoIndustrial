import { createFileRoute } from "@tanstack/react-router";

import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/")({
  component: () => (
    <main className="grid min-h-svh place-items-center">
      <Button>Automação Industrial</Button>
    </main>
  ),
});
