import type {
  IngestResponse,
  Ingestao,
  IngestaoExecucao,
  IngestaoLinha,
  IngestaoLinhaEvento,
  IngestaoLinhaStatus,
  IngestaoResumo,
} from "../core/entities/ingestao";
import type { PaginatedResponse } from "../core/types/common";
import { API_BASE, requestBlob, requestJson } from "./http";

export function getIngestionsPage(
  page: number,
  size: number,
  signal?: AbortSignal,
): Promise<PaginatedResponse<Ingestao>> {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  return requestJson(`${API_BASE}/ingestoes/?${params.toString()}`, signal);
}

export function getIngestionSummary(id: string, signal?: AbortSignal): Promise<IngestaoResumo> {
  return requestJson(`${API_BASE}/ingestoes/${id}/resumo`, signal);
}

export function getIngestionExecutions(id: string, signal?: AbortSignal): Promise<IngestaoExecucao[]> {
  return requestJson(`${API_BASE}/ingestoes/${id}/execucoes`, signal);
}

export function getIngestionLines(
  id: string,
  page: number,
  size: number,
  status?: IngestaoLinhaStatus | "",
  termo?: string,
  signal?: AbortSignal,
): Promise<PaginatedResponse<IngestaoLinha>> {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  if (status) params.set("status", status);
  if (termo?.trim()) params.set("termo", termo.trim());
  return requestJson(`${API_BASE}/ingestoes/${id}/linhas?${params.toString()}`, signal);
}

export function getIngestionLineEvents(
  id: string,
  lineId: string,
  signal?: AbortSignal,
): Promise<IngestaoLinhaEvento[]> {
  return requestJson(`${API_BASE}/ingestoes/${id}/linhas/${lineId}/eventos`, signal);
}

export function uploadIngestion(file: File): Promise<IngestResponse> {
  const body = new FormData();
  body.append("arquivo", file);
  return requestJson(`${API_BASE}/ingest`, undefined, { method: "POST", body });
}

export function resumeIngestion(id: string): Promise<IngestResponse> {
  return requestJson(`${API_BASE}/ingestoes/${id}/retomar`, undefined, { method: "POST" });
}

export function downloadSanitizedIngestion(id: string): Promise<Blob> {
  return requestBlob(`${API_BASE}/ingestoes/${id}/arquivo`);
}
