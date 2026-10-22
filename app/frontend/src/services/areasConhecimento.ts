import type { AreaConhecimento } from "../core/entities/areaConhecimento";
import type { PaginatedResponse } from "../core/types/common";
import { API_BASE, requestJson } from "./http";

export function getKnowledgeAreasPage(page: number, size: number, signal?: AbortSignal) {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  return requestJson<PaginatedResponse<AreaConhecimento>>(`${API_BASE}/areas-conhecimento/?${params}`, signal);
}
