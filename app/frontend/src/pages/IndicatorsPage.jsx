import BarList from "../componentes/graficos/BarList.jsx";
import PanelHeader from "../componentes/ui/PanelHeader.jsx";
import PopulationRateList from "../componentes/graficos/PopulationRateList.jsx";

const rows = (items, key) => (items || []).map((item) => ({ label: item[key], total: item.total }));

export default function IndicatorsPage({ report }) {
  return (
    <>
    <section className="analytics-grid lower-grid">
      <article className="panel"><PanelHeader title="Bolsas por grande área" subtitle="Nível superior da hierarquia do conhecimento" action=""/><BarList items={rows(report.por_grande_area, "grande_area").slice(0, 10)} tone="violet"/></article>
      <article className="panel"><PanelHeader title="Bolsas por área" subtitle="Áreas vinculadas às grandes áreas" action=""/><BarList items={rows(report.por_area, "area").slice(0, 10)} tone="teal"/></article>
      <article className="panel full-panel"><PanelHeader title="Bolsas por subárea" subtitle="Detalhamento da hierarquia do conhecimento" action=""/><BarList items={(report.por_subarea || []).slice(0, 15).map((item) => ({ label: item.subarea, detail: item.area, total: item.total }))} tone="violet" detailKey="detail" emptyMessage="Nenhuma bolsa está vinculada a uma subárea no conjunto atual."/><div className="indicator-note">Os indicadores respeitam os filtros de ano, modalidade, cidade, instituição, área, grande área e território. O total inclui bolsas regulares, resolvidas e pendentes de revisão; descartadas ficam fora.</div></article>
    </section>
    <section className="analytics-grid">
      <article className="panel"><PanelHeader title="Bolsas por população — municípios" subtitle="Taxa de bolsas a cada 10 mil habitantes · 12 maiores taxas" action=""/><PopulationRateList items={report.por_cidade} labelKey="cidade"/></article>
      <article className="panel"><PanelHeader title="Bolsas por população — territórios" subtitle="Taxa por 10 mil habitantes do território de identidade" action=""/><PopulationRateList items={report.por_territorio_identidade} labelKey="territorio_identidade"/></article>
      <p className="indicator-note full-panel">A taxa relaciona a quantidade de bolsas no recorte atual à população estimada. Ela complementa a contagem absoluta e não representa a proporção de pessoas que receberam bolsa.</p>
    </section>
    </>
  );
}
