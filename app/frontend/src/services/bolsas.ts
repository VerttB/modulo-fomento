import type { Bolsa } from "../core/entities/bolsa";
import type { PaginatedResponse } from "../core/types/common";
import type { ScholarshipFilters } from "../core/types/filters";
import type { ScholarshipReport } from "../core/types/reports";
import { API_BASE, requestJson } from "./http";
import { filterParams } from "./filtrosBolsas";

export async function getStatistics(
  filters: ScholarshipFilters,
  signal?: AbortSignal,
): Promise<ScholarshipReport> {
  const params = filterParams(filters);
  const query = params.size ? `?${params.toString()}` : "";
  return requestJson(`${API_BASE}/bolsas/estatisticas${query}`, signal);
}
export async function getScholarshipPage(
  page: number,
  size: number,
  filters: ScholarshipFilters,
  signal?: AbortSignal,
  search = "",
): Promise<PaginatedResponse<Bolsa>> {
  const params = filterParams(filters);
  params.set("page", String(page));
  params.set("size", String(size));
  params.set("incluir_conflitos", "true");
  if (search.trim()) params.set("termo", search.trim());
  return requestJson(`${API_BASE}/bolsas/?${params.toString()}`, signal);
}
