import { formatNumber } from "../../utils/format.js";
import EmptyState from "../ui/EmptyState.jsx";

export default function BarList({ items, tone, labelKey = "label", detailKey = null, emptyMessage }) {
  if (!items.length) return <EmptyState message={emptyMessage || "Nenhum resultado para os filtros selecionados."} />;
  const max = Math.max(...items.map((item) => item.total), 1);
  return (
    <div className="bar-list">
      {items.map((item, index) => (
        <div className="bar-item" key={`${item[labelKey]}-${index}`}>
          <div className="bar-meta">
            <span className="bar-rank">{String(index + 1).padStart(2, "0")}</span>
            <span className="bar-label">{item[labelKey]}{detailKey && item[detailKey] && <small>{item[detailKey]}</small>}</span>
            <strong>{formatNumber(item.total)}</strong>
          </div>
          <div className="bar-track"><span className={tone} style={{ width: `${Math.max((item.total / max) * 100, 3)}%` }} /></div>
        </div>
      ))}
    </div>
  );
}
