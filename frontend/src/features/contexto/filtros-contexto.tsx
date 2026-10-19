import { SlidersHorizontal, X } from "lucide-react";
import { useState } from "react";

import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SelectOpcoes } from "@/components/select-opcoes";
import { ComboboxEquipamento, ComboboxFabricante, ComboboxFamilia } from "@/features/catalogo/comboboxes";
import { IDIOMAS, ROTULO_IDIOMA, ROTULO_TIPO_DOCUMENTO, TIPOS_DOCUMENTO } from "@/lib/rotulos";

import { contarFiltros, type Contexto } from "./esquema";

interface FiltrosContextoProps {
  contexto: Contexto;
  aoMudar: (contexto: Contexto) => void;
  abertoInicialmente?: boolean;
}

export function FiltrosContexto({ contexto, aoMudar, abertoInicialmente = false }: FiltrosContextoProps) {
  const [aberto, setAberto] = useState(abertoInicialmente || contarFiltros(contexto) > 0);
  const total = contarFiltros(contexto);
  const mudar = (parcial: Partial<Contexto>) => {
    aoMudar({ ...contexto, ...parcial });
  };

  return (
    <section aria-label="Filtros de contexto" className="rounded-lg border">
      <div className="flex items-center gap-2 px-3 py-2">
        <Button
          variant="ghost"
          size="sm"
          aria-expanded={aberto}
          onClick={() => {
            setAberto((valor) => !valor);
          }}
        >
          <SlidersHorizontal />
          Contexto
          {total > 0 && (
            <span className="rounded-full bg-primary px-1.5 text-xs text-primary-foreground">{total}</span>
          )}
        </Button>
        <span className="hidden text-xs text-muted-foreground sm:inline">
          Restrinja a fabricante, família, equipamento, tipo de documento, idioma ou firmware.
        </span>
        <div className="flex-1" />
        {total > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              aoMudar({});
            }}
          >
            <X /> Limpar
          </Button>
        )}
      </div>
      {aberto && (
        <div className="grid gap-3 border-t p-3 sm:grid-cols-2 lg:grid-cols-3">
          <div className="grid gap-1.5">
            <Label htmlFor="filtro-fabricante">Fabricante</Label>
            <ComboboxFabricante
              id="filtro-fabricante"
              valor={contexto.id_fabricante}
              aoMudar={(id) => {
                mudar({ id_fabricante: id, id_familia: undefined, id_equipamento: undefined });
              }}
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="filtro-familia">Família</Label>
            <ComboboxFamilia
              id="filtro-familia"
              valor={contexto.id_familia}
              idFabricante={contexto.id_fabricante}
              aoMudar={(id) => {
                mudar({ id_familia: id, id_equipamento: undefined });
              }}
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="filtro-equipamento">Equipamento</Label>
            <ComboboxEquipamento
              id="filtro-equipamento"
              valor={contexto.id_equipamento}
              idFamilia={contexto.id_familia}
              aoMudar={(id) => {
                mudar({ id_equipamento: id });
              }}
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="filtro-tipo">Tipo de documento</Label>
            <SelectOpcoes
              id="filtro-tipo"
              valor={contexto.tipo_documento}
              aoMudar={(valor) => {
                mudar({ tipo_documento: valor });
              }}
              opcoes={TIPOS_DOCUMENTO}
              rotulos={ROTULO_TIPO_DOCUMENTO}
              rotuloTodos="Todos os tipos"
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="filtro-idioma">Idioma</Label>
            <SelectOpcoes
              id="filtro-idioma"
              valor={contexto.idioma}
              aoMudar={(valor) => {
                mudar({ idioma: valor });
              }}
              opcoes={IDIOMAS}
              rotulos={ROTULO_IDIOMA}
              rotuloTodos="Todos os idiomas"
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="filtro-firmware">Versão de firmware</Label>
            <Input
              key={contexto.versao_firmware ?? ""}
              id="filtro-firmware"
              placeholder="ex.: 4.7 SP14"
              maxLength={30}
              defaultValue={contexto.versao_firmware ?? ""}
              onBlur={(e) => {
                const valor = e.target.value.trim();
                if (valor !== (contexto.versao_firmware ?? ""))
                  mudar({ versao_firmware: valor || undefined });
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") e.currentTarget.blur();
              }}
            />
          </div>
        </div>
      )}
    </section>
  );
}
