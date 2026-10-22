import type { Unidade } from "../core/entities/unidade";
import type { PaginatedResponse } from "../core/types/common";
import { API_BASE, requestJson } from "./http";

export function getUnitsPage(page: number, size: number, signal?: AbortSignal) {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  return requestJson<PaginatedResponse<Unidade>>(`${API_BASE}/unidades/?${params}`, signal);
}
