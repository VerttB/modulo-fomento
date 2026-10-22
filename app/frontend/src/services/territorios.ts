import type { CidadeBahia } from "../core/entities/territorio";
import { API_BASE, requestJson } from "./http";

export interface TerritorySyncResult {
  territorios_atualizados: number;
  territorios_removidos: number;
  cidades_sem_correspondencia: number;
  metricas_atualizadas: boolean;
}

export function getCities(signal?: AbortSignal): Promise<CidadeBahia[]> {
  return requestJson(`${API_BASE}/territorios/cidades`, signal);
}

export function synchronizeResearcherTerritories(): Promise<TerritorySyncResult> {
  return requestJson(`${API_BASE}/territorios/sincronizar-pesquisadores`, undefined, {
    method: "POST",
  });
}
