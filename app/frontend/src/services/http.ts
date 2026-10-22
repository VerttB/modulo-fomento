import type { ApiErrorBody } from "../core/types/common";

const configuredApiBase = import.meta.env.VITE_API_BASE_URL;

if (!configuredApiBase) {
  throw new Error("Configure VITE_API_BASE_URL com a URL absoluta da API.");
}

export const API_BASE = new URL(configuredApiBase).toString().replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function request(path: string, options: RequestInit = {}): Promise<Response> {
  const response = await fetch(path, options);
  if (!response.ok) {
    let detail = "Não foi possível concluir a operação.";
    try {
      const body = (await response.json()) as ApiErrorBody;
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // Mantém uma mensagem simples se a resposta não tiver JSON.
    }
    throw new ApiError(detail, response.status);
  }
  return response;
}

export async function requestJson<T>(
  path: string,
  signal?: AbortSignal,
  options: Omit<RequestInit, "signal"> = {},
): Promise<T> {
  const response = await request(path, { ...options, signal });
  return (await response.json()) as T;
}

export async function requestBlob(path: string, options: RequestInit = {}): Promise<Blob> {
  const response = await request(path, options);
  return response.blob();
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 503) {
    return "A API está temporariamente indisponível. Tente novamente em instantes.";
  }
  return error instanceof Error ? error.message : "Falha ao conectar com a API.";
}
