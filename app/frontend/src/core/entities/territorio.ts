export interface TerritorioIdentidade {
  id: string;
  nome: string;
  nome_normalizado: string;
}

export interface CidadeBahia {
  cidade: string;
  populacao_estimada: number;
  territorio_identidade: string;
}
