import type { Projeto } from "../core/entities/projeto";
import type { PaginatedResponse } from "../core/types/common";
import { API_BASE, requestJson } from "./http";

export function getProjectsPage(
  page: number,
  size: number,
  search = "",
  signal?: AbortSignal,
): Promise<PaginatedResponse<Projeto>> {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  if (search.trim()) params.set("termo", search.trim());
  return requestJson(`${API_BASE}/projetos/?${params.toString()}`, signal);
}
