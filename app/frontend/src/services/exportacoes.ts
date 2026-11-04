import type { ScholarshipFilters } from "../core/types/filters";
import { filterParams } from "./filtrosBolsas";
import { API_BASE, requestBlob } from "./http";

export type ExportFormat = "csv" | "xlsx" | "json";
export type ExportDimension = "territorio" | "cidade" | "instituicao";

const exportAccept: Record<ExportFormat, string> = {
  csv: "text/csv",
  xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  json: "application/json",
};

export async function exportScholarships(filters: ScholarshipFilters, search = "", format: ExportFormat = "csv", signal?: AbortSignal): Promise<Blob> {
  const params = filterParams(filters);
  if (search.trim()) params.set("termo", search.trim());
  return requestBlob(`${API_BASE}/exportacoes/bolsistas/registros?${params}`, {
    signal, headers: { Accept: exportAccept[format] },
  });
}

export async function exportScholarshipSummary(filters: ScholarshipFilters, dimensions: ExportDimension[], format: ExportFormat = "csv", signal?: AbortSignal): Promise<Blob> {
  const params = filterParams(filters);
  dimensions.forEach((dimension) => params.append("recorte", dimension));
  return requestBlob(`${API_BASE}/exportacoes/bolsistas/resumo?${params}`, {
    signal, headers: { Accept: exportAccept[format] },
  });
}
