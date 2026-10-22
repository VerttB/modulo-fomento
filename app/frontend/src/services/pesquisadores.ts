import type { Pesquisador } from "../core/entities/pesquisador";
import type { PaginatedResponse } from "../core/types/common";
import { API_BASE, requestJson } from "./http";

export function getResearchersPage(
  page: number,
  size: number,
  search = "",
  signal?: AbortSignal,
): Promise<PaginatedResponse<Pesquisador>> {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  if (search.trim()) params.set("termo", search.trim());
  return requestJson(`${API_BASE}/pesquisadores/?${params.toString()}`, signal);
}
