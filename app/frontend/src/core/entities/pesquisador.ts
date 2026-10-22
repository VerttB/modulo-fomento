export type PesquisadorStatus = "APROVADO" | "PENDENTE" | "REJEITADO";

export interface TerritorioIdentidadeResumo {
  id: string;
  nome: string;
  nome_normalizado: string;
}

export interface Pesquisador {
  id: string;
  lattes: string | null;
  nome: string | null;
  cidade: string | null;
  territorio_identidade_id: string | null;
  territorio_identidade: TerritorioIdentidadeResumo | null;
  cep_referencia: string | null;
  status: PesquisadorStatus;
}
