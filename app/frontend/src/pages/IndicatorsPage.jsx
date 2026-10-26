import BarList from "../componentes/graficos/BarList.jsx";
import PanelHeader from "../componentes/ui/PanelHeader.jsx";
import PopulationRateList from "../componentes/graficos/PopulationRateList.jsx";

const rows = (items, key) => (items || []).map((item) => ({ label: item[key], total: item.total }));

export default function IndicatorsPage({ report }) {
  return (
    <>
    <section className="analytics-grid lower-grid">
      <article className="panel"><PanelHeader title="Bolsistas por grande área" subtitle="Nível superior da hierarquia do conhecimento" action=""/><BarList items={rows(report.por_grande_area, "grande_area").slice(0, 10)} tone="violet"/></article>
      <article className="panel"><PanelHeader title="Bolsistas por área" subtitle="Áreas vinculadas às grandes áreas" action=""/><BarList items={rows(report.por_area, "area").slice(0, 10)} tone="teal"/></article>
      <article className="panel full-panel"><PanelHeader title="Bolsistas por subárea" subtitle="Detalhamento da hierarquia do conhecimento" action=""/><BarList items={(report.por_subarea || []).slice(0, 15).map((item) => ({ label: item.subarea, detail: item.area, total: item.total }))} tone="violet" detailKey="detail" emptyMessage="Nenhum registro de bolsista está vinculado a uma subárea no conjunto atual."/><div className="indicator-note">Os indicadores respeitam os filtros de ano, modalidade, município, instituição, área, grande área e território. O total inclui registros regulares, resolvidos e pendentes de revisão; descartados ficam fora.</div></article>
    </section>
    <section className="analytics-grid">
      <article className="panel"><PanelHeader title="Bolsistas por população — municípios" subtitle="Registros a cada 10 mil habitantes · 12 maiores taxas" action=""/><PopulationRateList items={report.por_cidade} labelKey="cidade"/></article>
      <article className="panel"><PanelHeader title="Bolsistas por população — territórios" subtitle="Registros a cada 10 mil habitantes do território de identidade" action=""/><PopulationRateList items={report.por_territorio_identidade} labelKey="territorio_identidade"/></article>
      <p className="indicator-note full-panel">A taxa relaciona a quantidade de registros de bolsistas no recorte atual à população estimada. Ela complementa a contagem absoluta e não representa a proporção de pessoas que receberam apoio.</p>
    </section>
    </>
  );
}
