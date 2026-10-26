import { formatNumber } from "../../utils/format.js";
import EmptyState from "../ui/EmptyState.jsx";

const formatRate = (value) => new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
}).format(value || 0);

export default function PopulationRateList({ items = [], labelKey, emptyMessage }) {
  const rows = items
    .filter((item) => item.bolsas_por_10_mil_habitantes != null
      && Number.isFinite(Number(item.bolsas_por_10_mil_habitantes))
      && item.populacao_estimada > 0)
    .sort((a, b) => b.bolsas_por_10_mil_habitantes - a.bolsas_por_10_mil_habitantes)
    .slice(0, 12);
  if (!rows.length) return <EmptyState message={emptyMessage || "Sem população de referência para calcular a taxa."} />;
  const max = Math.max(...rows.map((item) => item.bolsas_por_10_mil_habitantes), 1);
  return <div className="population-rate-list">
    {rows.map((item, index) => <div className="population-rate-row" key={`${item[labelKey]}-${index}`}>
      <div className="population-rate-meta">
        <span className="bar-rank">{String(index + 1).padStart(2, "0")}</span>
        <strong>{item[labelKey] || "Não identificado"}</strong>
        <span>{formatRate(item.bolsas_por_10_mil_habitantes)} / 10 mil</span>
      </div>
      <div className="bar-track"><span style={{ width: `${Math.max((item.bolsas_por_10_mil_habitantes / max) * 100, 3)}%` }} /></div>
      <small>{formatNumber(item.total)} registros de bolsistas · população {formatNumber(item.populacao_estimada)}</small>
    </div>)}
  </div>;
}
