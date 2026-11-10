import { formatDate, formatNumber } from "../../utils/format";

export function TruncationNotice({ truncated }) {
  if (!truncated) return null;
  return <small className="maria-block-notice">Resultado limitado pela fonte: nem todos os registros encontrados aparecem aqui.</small>;
}

export function OriginFooter({ origin }) {
  if (!origin) return null;
  const parts = [];
  if (origin.sources?.length) parts.push(`Fonte: ${origin.sources.join(" e ")}`);
  if (origin.description) parts.push(origin.description);
  const queriedAt = origin.queried_at ? formatDate(origin.queried_at) : null;
  if (queriedAt) parts.push(`consultado em ${queriedAt}`);
  if (origin.coverage) parts.push(`${formatNumber(origin.coverage.found)} de ${formatNumber(origin.coverage.keys)} encontrados`);
  if (!parts.length) return null;
  return <small className="maria-block-notice">{parts.join(" · ")}</small>;
}
