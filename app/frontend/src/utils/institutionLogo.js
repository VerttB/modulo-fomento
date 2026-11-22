import { publicAssetUrl } from "./publicAssetUrl.js";

/**
 * Logos das instituições — **somente as que existem no Observatório**.
 *
 * Arquivos originais: `observatorio-front/public/university-logo/LOGO-*.png`
 * Convertidos para WebP (≤ 400px) em `public/instituicoes/`.
 *
 * Se a instituição não estiver neste catálogo, a interface usa as iniciais
 * (classe `.person-avatar`) — nada de fallback genérico.
 */
const LOGOS = {
  UFBA: "LOGO-UFBA",
  UFSB: "LOGO-UFSB",
  UESC: "LOGO-UESC",
  UESB: "LOGO-UESB",
  UEFS: "LOGO-UEFS",
  UFRB: "LOGO-UFRB",
  UFOB: "LOGO-UFOB",
  UNEB: "LOGO-UNEB",
  IFBA: "LOGO-IFBA",
  FIOCRUZ: "LOGO-FIOCRUZ",
  EBMSP: "LOGO-EBMSP",
};

const normalize = (value) => (value || "")
  .toString()
  .normalize("NFD")
  .replace(/[\u0300-\u036f]/g, "")
  .replace(/[^A-Z0-9]/gi, "")
  .toUpperCase();

/** Procura correspondência exata por sigla ou parte do nome. */
function matchLogo(value) {
  const normalized = normalize(value);
  if (!normalized) return null;
  if (LOGOS[normalized]) return LOGOS[normalized];
  // Tenta cada token da sigla/nome (ex.: "IHAC - UFBA" → "UFBA")
  const parts = String(value || "")
    .split(/[^A-Za-z0-9]+/)
    .map((part) => normalize(part))
    .filter(Boolean)
    .sort((a, b) => b.length - a.length);
  for (const part of parts) {
    if (LOGOS[part]) return LOGOS[part];
  }
  return null;
}

export function institutionLogo(institution) {
  if (!institution) return null;
  const fromSigla = matchLogo(institution.sigla);
  if (fromSigla) return publicAssetUrl(`instituicoes/${fromSigla}.webp`);
  const fromName = matchLogo(institution.nome);
  if (fromName) return publicAssetUrl(`instituicoes/${fromName}.webp`);
  return null;
}

export function institutionInitials(institution) {
  return (institution?.sigla || institution?.nome || "?").slice(0, 2).toUpperCase();
}