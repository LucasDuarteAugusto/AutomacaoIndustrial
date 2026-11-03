import { Controller, type Control, type FieldPath, type FieldValues } from "react-hook-form";

import { Label } from "@/components/ui/label";

/** Checkbox "Ativo" ligado ao react-hook-form. */
export function CampoAtivo<T extends FieldValues>({
  control,
  name = "ativo" as FieldPath<T>,
  erro,
}: {
  control: Control<T>;
  name?: FieldPath<T>;
  erro?: string | undefined;
}) {
  const id = `campo-${name}`;
  return (
    <div className="grid gap-1.5">
      <Label htmlFor={id}>Situação</Label>
      <Controller
        control={control}
        name={name}
        render={({ field }) => (
          <label className="flex h-9 items-center gap-2 text-sm">
            <input
              id={id}
              type="checkbox"
              className="size-4 accent-primary"
              checked={Boolean(field.value)}
              onChange={(e) => {
                field.onChange(e.target.checked);
              }}
              onBlur={field.onBlur}
              ref={field.ref}
              aria-invalid={erro ? true : undefined}
            />
            Cadastro ativo
          </label>
        )}
      />
      {erro && (
        <p role="alert" className="text-xs text-destructive">
          {erro}
        </p>
      )}
    </div>
  );
}
