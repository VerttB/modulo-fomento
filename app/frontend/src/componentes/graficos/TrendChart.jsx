import { formatNumber } from "../../utils/format.js";
import EmptyState from "../ui/EmptyState.jsx";

export default function TrendChart({ values }) {
  if (!values.length) return <EmptyState message="Não há registros de bolsistas com data inicial para o recorte selecionado." />;
  const orderedValues = [...values].sort((a, b) => Number(a.ano) - Number(b.ano));
  const max = Math.max(...orderedValues.map((item) => Number(item.total)), 1);
  const xFor = (index) => orderedValues.length === 1 ? 298 : 48 + index * (500 / (orderedValues.length - 1));
  const yFor = (item) => 151 - (Number(item.total) / max) * 112;
  const points = orderedValues.map((item, index) => `${xFor(index)},${yFor(item)}`).join(" ");
  return (
    <div className="chart-wrap">
      <div className="y-labels"><span>{formatNumber(max)}</span><span>{formatNumber(Math.round(max / 2))}</span><span>0</span></div>
      <svg className="line-chart" viewBox="0 0 560 180" preserveAspectRatio="none" role="img" aria-label="Registros de bolsistas por ano">
        <defs><linearGradient id="areaFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#138b83" stopOpacity=".18"/><stop offset="100%" stopColor="#138b83" stopOpacity="0"/></linearGradient></defs>
        <line x1="35" y1="39" x2="548" y2="39"/><line x1="35" y1="94" x2="548" y2="94"/><line x1="35" y1="151" x2="548" y2="151"/>
        <polygon points={`48,151 ${points} 548,151`} fill="url(#areaFill)"/><polyline points={points} fill="none" stroke="#07877f" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
        {orderedValues.map((item, index) => <circle key={item.ano} cx={xFor(index)} cy={yFor(item)} r="4.5" fill="white" stroke="#07877f" strokeWidth="3"><title>{item.ano}: {formatNumber(item.total)} registros de bolsistas</title></circle>)}
      </svg>
      <div className="x-labels">{orderedValues.map((item, index) => <span key={item.ano}>{index === 0 || index === orderedValues.length - 1 || Number(item.ano) % 5 === 0 ? item.ano : ""}</span>)}</div>
    </div>
  );
}
