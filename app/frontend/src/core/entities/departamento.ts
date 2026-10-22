export interface Departamento {
  id: string;
  nome: string | null;
  unidade: string | null;
  cep: string | null;
  instituicao_id: string;
  grande_area_id: string | null;
}
