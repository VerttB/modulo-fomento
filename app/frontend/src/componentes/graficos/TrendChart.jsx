import { formatNumber } from "../../utils/format.js";
import EmptyState from "../ui/EmptyState.jsx";
import { useState } from "react";

export default function TrendChart({ values }) {
  if (!values.length) return <EmptyState message="Não há registros de bolsistas com data inicial para o recorte selecionado." />;

  const orderedValues = [...values].sort((a, b) => Number(a.ano) - Number(b.ano));
  const max = Math.max(...orderedValues.map((item) => Number(item.total)), 1);
  const xFor = (index) => orderedValues.length === 1 ? 298 : 48 + index * (500 / (orderedValues.length - 1));
  const yFor = (item) => 151 - (Number(item.total) / max) * 112;
  const points = orderedValues.map((item, index) => `${xFor(index)},${yFor(item)}`).join(" ");

  const [showTable, setShowTable] = useState(false);

  return (
    <div className="trend-chart-container">
      <div className="chart-wrap">
        {!showTable && (
          <>
            <div className="y-labels"><span>{formatNumber(max)}</span><span>{formatNumber(Math.round(max / 2))}</span><span>0</span></div>
            <svg className="line-chart" viewBox="0 0 560 180" preserveAspectRatio="none" role="img" aria-label="Registros de bolsistas por ano">
              <defs><linearGradient id="areaFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" style={{ stopColor: "var(--chart-1)", stopOpacity: ".18" }}/><stop offset="100%" style={{ stopColor: "var(--chart-1)", stopOpacity: "0" }}/></linearGradient></defs>
              <line x1="35" y1="39" x2="548" y2="39"/><line x1="35" y1="94" x2="548" y2="94"/><line x1="35" y1="151" x2="548" y2="151"/>
              <polygon points={`48,151 ${points} 548,151`} fill="url(#areaFill)"/>
              <polyline points={points} fill="none" style={{ stroke: "var(--chart-1)" }} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
              {orderedValues.map((item, index) => <circle key={item.ano} cx={xFor(index)} cy={yFor(item)} r="4.5" fill="white" style={{ stroke: "var(--chart-1)" }} strokeWidth="3"><title>{item.ano}: {formatNumber(item.total)} registros de bolsistas</title></circle>)}
            </svg>
            <div className="x-labels">{orderedValues.map((item, index) => <span key={item.ano}>{index === 0 || index === orderedValues.length - 1 || Number(item.ano) % 5 === 0 ? item.ano : ""}</span>)}</div>
          </>
        )}

        {showTable && (
          <div className="chart-data-table" role="region" aria-label="Dados da evolução do fomento em tabela">
            <table>
              <caption>Registros de bolsistas por ano de início</caption>
              <thead><tr><th scope="col">Ano</th><th scope="col">Registros de bolsistas</th></tr></thead>
              <tbody>{orderedValues.map((item) => <tr key={item.ano}><th scope="row">{item.ano}</th><td>{formatNumber(item.total)}</td></tr>)}</tbody>
            </table>
          </div>
        )}
      </div>

      <button
        type="button"
        className="chart-toggle"
        onClick={() => setShowTable(!showTable)}
        aria-pressed={showTable}
      >
        {showTable ? "Ver gráfico" : "Ver os dados em tabela"}
      </button>
    </div>
  );
}