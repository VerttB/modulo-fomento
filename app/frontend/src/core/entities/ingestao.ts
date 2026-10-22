export type IngestaoStatus = "PROCESSANDO" | "CONCLUIDA" | "FALHA";
export type IngestaoLinhaStatus =
  | "PENDENTE"
  | "INSERIDA"
  | "INSERIDA_CONFLITO"
  | "DUPLICADA"
  | "IGNORADA"
  | "INVALIDA"
  | "ERRO";

export interface Ingestao {
  id: string;
  nome_arquivo: string;
  quantidade_linhas: number;
  tipo: string;
  status: IngestaoStatus;
  iniciada_em: string;
  finalizada_em: string | null;
  linhas_processadas: number;
  linhas_duplicadas: number;
  linhas_ignoradas: number;
  bolsas_conflitantes: number;
  pesquisadores_consultados: number;
  pesquisadores_total: number;
}

export interface IngestaoResumo {
  ingestao_id: string;
  total_linhas: number;
  por_status: Partial<Record<IngestaoLinhaStatus, number>>;
  total_execucoes: number;
}

export interface IngestaoLinha {
  id: string;
  linha_origem: number;
  status: IngestaoLinhaStatus;
  motivo: string | null;
  linha_duplicada: number | null;
  atualizada_em: string;
  lattes_id: string | null;
  pesquisador_id: string | null;
  pesquisador_nome: string | null;
  projeto_id: string | null;
  projeto_nome: string | null;
  bolsa_id: string | null;
  modalidade: string | null;
  quando_iniciou: string | null;
  quando_terminou: string | null;
  instituicao_nome: string | null;
  bolsa_status: string | null;
  is_conflict: boolean | null;
  bolsas_conflitantes: IngestaoBolsaConflito[];
}

export interface IngestaoBolsaConflito {
  id: string;
  status: string;
  motivo: string;
  bolsa_id: string;
  modalidade: string | null;
  quando_iniciou: string | null;
  quando_terminou: string | null;
  projeto_nome: string | null;
}

export interface IngestaoExecucao {
  id: string;
  numero: number;
  status: IngestaoStatus;
  iniciada_em: string;
  finalizada_em: string | null;
  erro: string | null;
}

export interface IngestaoLinhaEvento {
  id: string;
  execucao_id: string;
  execucao_numero: number | null;
  status: IngestaoLinhaStatus;
  motivo: string | null;
  bolsa_id: string | null;
  pesquisador_id: string | null;
  projeto_id: string | null;
  criado_em: string;
  projeto_nome: string | null;
  pesquisador_nome: string | null;
}

export interface IngestResponse {
  ingestao_id: string;
  linhas_processadas: number;
  linhas_duplicadas: number;
  linhas_ignoradas: number;
  bolsas_conflitantes: number;
  pesquisadores_consultados: number;
  erros: string[];
}
