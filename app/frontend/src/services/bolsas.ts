import type { Bolsa } from "../core/entities/bolsa";
import type { PaginatedResponse } from "../core/types/common";
import type { ScholarshipFilters } from "../core/types/filters";
import type { ScholarshipReport } from "../core/types/reports";
import { API_BASE, requestBlob, requestJson } from "./http";

const filterFields: Record<keyof ScholarshipFilters, string> = {
  from: "ano_inicio",
  to: "ano_fim",
  modality: "modalidade",
  city: "cidade",
  institution: "instituicao",
  area: "area",
  largeArea: "grande_area",
  territory: "territorio_identidade",
};

function filterParams(filters: ScholarshipFilters, institutionParameter: string): URLSearchParams {
  const params = new URLSearchParams();
  for (const [key, apiField] of Object.entries(filterFields) as Array<
    [keyof ScholarshipFilters, string]
  >) {
    const value = filters[key].trim();
    if (value) params.set(key === "institution" ? institutionParameter : apiField, value);
  }
  return params;
}

export async function getStatistics(
  filters: ScholarshipFilters,
  signal?: AbortSignal,
): Promise<ScholarshipReport> {
  const params = filterParams(filters, "instituicao");
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
  const params = filterParams(filters, "universidade");
  params.set("page", String(page));
  params.set("size", String(size));
  params.set("incluir_conflitos", "true");
  if (search.trim()) params.set("termo", search.trim());
  return requestJson(`${API_BASE}/bolsas/?${params.toString()}`, signal);
}

export async function exportScholarships(
  filters: ScholarshipFilters,
  search = "",
  signal?: AbortSignal,
): Promise<Blob> {
  const params = filterParams(filters, "universidade");
  if (search.trim()) params.set("termo", search.trim());
  return requestBlob(`${API_BASE}/bolsas/exportar?${params.toString()}`, { signal });
}
