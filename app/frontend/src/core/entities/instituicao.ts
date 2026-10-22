import type { ScholarshipReport } from "../types/reports";

export interface Instituicao {
  id: string;
  nome: string | null;
  cep: string | null;
  sigla: string | null;
}

export interface InstituicaoPerfil {
  instituicao: Instituicao;
  total_pesquisadores: number;
  total_projetos: number;
  estatisticas: ScholarshipReport;
}

export interface BolsaInstituicao {
  id: string;
  quando_iniciou: string | null;
  quando_terminou: string | null;
  modalidade: string | null;
  nome_curso: string | null;
  status: string;
  is_conflict: boolean;
  pesquisador_nome: string | null;
  pesquisador_cidade: string | null;
  projeto_nome: string | null;
}
