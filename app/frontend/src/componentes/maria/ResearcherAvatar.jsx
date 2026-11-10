import { useState } from "react";
import { researcherImageUrl } from "../../services/simcc";

function PersonIcon() {
  return <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="8" r="4" />
    <path d="M4 20c0-4 3.6-6.5 8-6.5s8 2.5 8 6.5" />
  </svg>;
}

// A foto vem do SIMCC pelo Lattes. Sem Lattes, sem URL configurada ou quando o
// SIMCC não tem a foto (404), mostra o ícone de pessoa no lugar.
export default function ResearcherAvatar({ lattesId }) {
  const src = researcherImageUrl(lattesId);
  const [failedSrc, setFailedSrc] = useState(null);

  if (!src || failedSrc === src) {
    return <span className="maria-avatar maria-avatar-icon" aria-hidden="true"><PersonIcon /></span>;
  }
  return <img className="maria-avatar" src={src} alt="" loading="lazy" decoding="async" onError={() => setFailedSrc(src)} />;
}
