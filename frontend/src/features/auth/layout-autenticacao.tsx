import type { ReactNode } from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { IconeMarca } from "@/features/layout/icone-marca";

export function LayoutAutenticacao({
  titulo,
  descricao,
  children,
}: {
  titulo: string;
  descricao: string;
  children: ReactNode;
}) {
  return (
    <main className="grid min-h-svh place-items-center bg-muted/40 p-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="flex items-center justify-center gap-2">
          <IconeMarca className="size-8" />
          <span className="text-lg font-semibold">DrivePilot</span>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">
              <h1>{titulo}</h1>
            </CardTitle>
            <CardDescription>{descricao}</CardDescription>
          </CardHeader>
          <CardContent>{children}</CardContent>
        </Card>
      </div>
    </main>
  );
}
