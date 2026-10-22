import type { BolsaInstituicao, Instituicao, InstituicaoPerfil } from "../core/entities/instituicao";
import type { Pesquisador } from "../core/entities/pesquisador";
import type { Projeto } from "../core/entities/projeto";
import type { PaginatedResponse } from "../core/types/common";
import { API_BASE, requestJson } from "./http";

export function getInstitutionsPage(page: number, size: number, term = "", signal?: AbortSignal) {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  if (term.trim()) params.set("termo", term.trim());
  return requestJson<PaginatedResponse<Instituicao>>(`${API_BASE}/instituicoes/?${params}`, signal);
}

export function getInstitutionProfile(id: string, signal?: AbortSignal) {
  return requestJson<InstituicaoPerfil>(`${API_BASE}/instituicoes/${id}/perfil`, signal);
}

function getInstitutionPage<T>(id: string, resource: string, page: number, size: number, signal?: AbortSignal) {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  return requestJson<PaginatedResponse<T>>(`${API_BASE}/instituicoes/${id}/${resource}?${params}`, signal);
}

export const getInstitutionResearchers = (id: string, page: number, size: number, signal?: AbortSignal) =>
  getInstitutionPage<Pesquisador>(id, "pesquisadores", page, size, signal);

export const getInstitutionProjects = (id: string, page: number, size: number, signal?: AbortSignal) =>
  getInstitutionPage<Projeto>(id, "projetos", page, size, signal);

export const getInstitutionScholarships = (id: string, page: number, size: number, signal?: AbortSignal) =>
  getInstitutionPage<BolsaInstituicao>(id, "bolsas", page, size, signal);
