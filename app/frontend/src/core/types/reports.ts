export interface MetricRow {
  total: number;
}

export interface NamedMetric extends MetricRow {
  cidade?: string;
  populacao_estimada?: number | null;
  bolsas_por_100_mil_habitantes?: number | null;
  bolsas_por_10_mil_habitantes?: number | null;
  territorio_identidade?: string | null;
  nome?: string | null;
  sigla?: string | null;
  grande_area?: string | null;
  area?: string | null;
  subarea?: string | null;
  ano?: number | null;
}

export interface ScholarshipReport {
  total: number;
  por_ano: Array<{ ano: number; total: number }>;
  por_modalidade: Record<string, number>;
  por_instituicao: NamedMetric[];
  por_cidade: NamedMetric[];
  por_territorio_identidade: NamedMetric[];
  por_grande_area: NamedMetric[];
  por_area: NamedMetric[];
  por_subarea: NamedMetric[];
}
