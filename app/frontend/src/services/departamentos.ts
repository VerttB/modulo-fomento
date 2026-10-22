import type { Departamento } from "../core/entities/departamento";
import type { PaginatedResponse } from "../core/types/common";
import { API_BASE, requestJson } from "./http";

export function getDepartmentsPage(page: number, size: number, signal?: AbortSignal) {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  return requestJson<PaginatedResponse<Departamento>>(`${API_BASE}/departamentos/?${params}`, signal);
}
