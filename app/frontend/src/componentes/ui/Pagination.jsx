import { formatNumber } from "../../utils/format.js";

export default function Pagination({ page, pages, total, onChange }) {
  if (pages <= 1) return <div className="pagination-summary">{formatNumber(total)} registro(s)</div>;
  return (
    <div className="pagination">
      <span>{formatNumber(total)} registros · página {page} de {pages}</span>
      <div>
        <button disabled={page <= 1} onClick={() => onChange(page - 1)}>← Anterior</button>
        <button disabled={page >= pages} onClick={() => onChange(page + 1)}>Próxima →</button>
      </div>
    </div>
  );
}
