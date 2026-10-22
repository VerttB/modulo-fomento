export type AreaConhecimentoTipo = "grande_area" | "area" | "subarea";

export interface AreaConhecimento {
  id: string;
  termo: string;
  termo_normalizado: string;
  tipo: AreaConhecimentoTipo;
  pai_id: string | null;
}
