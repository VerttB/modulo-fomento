import type { PalavraChave } from "../core/entities/palavraChave";
import type { PaginatedResponse } from "../core/types/common";
import { API_BASE, requestJson } from "./http";

export function getKeywordsPage(page: number, size: number, signal?: AbortSignal) {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  return requestJson<PaginatedResponse<PalavraChave>>(`${API_BASE}/palavras-chave/?${params}`, signal);
}
