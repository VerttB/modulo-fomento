import type { AreaConhecimentoTipo } from "./areaConhecimento";

export interface AreaConhecimentoResumo {
  id: string;
  termo: string;
  termo_normalizado: string;
  tipo: AreaConhecimentoTipo;
  pai_id: string | null;
}

export interface Projeto {
  id: string;
  nome: string | null;
  resumo: string | null;
  area_conhecimento_id: string | null;
  area_conhecimento: AreaConhecimentoResumo | null;
}
