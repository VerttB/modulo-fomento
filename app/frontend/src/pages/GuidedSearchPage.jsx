import { formatNumber } from "../utils/format.js";

const suggestions = [
  "Quantas bolsas foram concedidas no período?",
  "Quais municípios têm mais bolsistas?",
  "Como as bolsas se distribuem por modalidade?",
  "Quais instituições aparecem em destaque?",
];

export default function GuidedSearchPage({ query, answer, onChange, onSubmit, total, disabled }) {
  return <section className="maria-panel">
    <div className="maria-orb">✳</div><div className="eyebrow">CONSULTA AOS DADOS DA API</div><h2>Explore o relatório disponível</h2>
    <p>Esta consulta identifica modalidades, municípios, territórios e instituições já presentes nos agregados da API. Não é uma IA generativa.</p>
    <div className="suggestions"><span>EXPERIMENTE</span>{suggestions.map((item) => <button key={item} disabled={disabled} onClick={() => onSubmit(item)}>{item}<b>↗</b></button>)}</div>
    <form className="question-form" onSubmit={(event) => { event.preventDefault(); onSubmit(); }}><input value={query} onChange={(event) => onChange(event.target.value)} placeholder="Ex.: quantas bolsas há em Salvador?"/><button type="submit" disabled={disabled}>Consultar <span>↑</span></button></form>
    {answer && <div className="answer-card"><span className="answer-mark">✳</span><div><strong>Resultado do relatório</strong><p>{answer}</p></div></div>}
    <small className="maria-disclaimer">Base atual: {formatNumber(total)} bolsas no recorte. Os resultados são limitados aos campos agregados retornados pela API.</small>
  </section>;
}
