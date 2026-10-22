export type BolsaStatus = "REGULAR" | "PENDENTE_REVISAO" | "RESOLVIDA" | "DESCARTADA";

export interface Bolsa {
  id: string;
  quando_iniciou: string | null;
  quando_terminou: string | null;
  data_saida_pesquisador: string | null;
  cep_referencia: string | null;
  modalidade: string | null;
  nome_curso: string | null;
  projeto_id: string;
  instituicao_id: string;
  pesquisador_id: string;
  ingestao_id: string | null;
  linha_origem: number | null;
  is_conflict: boolean;
  status: BolsaStatus;
}
