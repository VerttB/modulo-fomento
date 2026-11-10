const SIMCC_API_BASE: string = (import.meta.env.VITE_SIMCC_API_URL ?? "").replace(/\/+$/, "");

/**
 * Endereço da foto do pesquisador no SIMCC, buscada pelo identificador Lattes.
 * Sem `VITE_SIMCC_API_URL` ou sem Lattes, devolve `null` e a interface mostra
 * o ícone no lugar da foto.
 */
export function researcherImageUrl(lattesId: string | null | undefined): string | null {
  const id = lattesId?.trim();
  if (!SIMCC_API_BASE || !id) return null;
  return `${SIMCC_API_BASE}/researcher/image?lattes_id=${encodeURIComponent(id)}`;
}
