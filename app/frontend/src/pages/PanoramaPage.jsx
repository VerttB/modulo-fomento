import BarList from "../componentes/graficos/BarList.jsx";
import TrendChart from "../componentes/graficos/TrendChart.jsx";
import MetricCard from "../componentes/ui/MetricCard.jsx";
import PanelHeader from "../componentes/ui/PanelHeader.jsx";

const rows = (items, key) => (items || []).map((item) => ({ label: item[key], total: item.total }));

export default function PanoramaPage({ report, totals, modalityRows, institutionRows, filters, onNavigate }) {
  return <>
    <section className="welcome-banner"><div className="welcome-copy"><div className="banner-eyebrow"><span /> OBSERVATÓRIO FAPESB</div><h2>Conhecimento que transforma<br />a Bahia, território por território.</h2><p>Acompanhe os registros de bolsistas e descubra quem está construindo o futuro da ciência baiana.</p><button onClick={() => onNavigate("indicadores")}>Explorar indicadores <span>↗</span></button></div><div className="banner-art" aria-hidden="true"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="orbit orbit-three"/><span className="star star-a">✳</span><span className="star star-b">✳</span><div className="art-core"><span>BA</span><small>ciência<br />em movimento</small></div></div></section>
    <section className="metric-grid">
      <MetricCard label="Registros de bolsistas" value={totals.total} hint="registros retornados pela API" icon="▤" accent="teal"/>
      <MetricCard label="Modalidades" value={totals.modalities} hint="categorias de apoio" icon="◉" accent="violet"/>
      <MetricCard label="Municípios" value={totals.cities} hint="com bolsistas apoiados" icon="⌖" accent="orange"/>
      <MetricCard label="Instituições" value={totals.institutions} hint="na rede de fomento" icon="⌂" accent="blue"/>
    </section>
    <section className="analytics-grid">
      <article className="panel trend-panel"><PanelHeader title="Evolução do fomento" subtitle="Registros de bolsistas por ano de início (API)" action={filters.from || filters.to ? `${filters.from || "início"} — ${filters.to || "atual"}` : "Todos os anos"}/><TrendChart values={report.por_ano || []}/></article>
      <article className="panel"><PanelHeader title="Modalidades" subtitle="Distribuição no recorte atual" action="Ver detalhes →" onAction={() => onNavigate("indicadores")}/><BarList items={modalityRows.slice(0, 5)} tone="teal"/></article>
    </section>
    <section className="analytics-grid lower-grid">
      <article className="panel territory-panel"><PanelHeader title="Presença nos territórios" subtitle="Distribuição de bolsistas por território" action="Ver detalhes →" onAction={() => onNavigate("territorios")}/><BarList items={rows(report.por_territorio_identidade, "territorio_identidade").slice(0, 6)} tone="teal" emptyMessage="A API não retornou territórios para este recorte."/></article>
      <article className="panel institution-panel"><PanelHeader title="Instituições em destaque" subtitle="Maior número de registros de bolsistas no recorte" action=""/><BarList items={institutionRows.slice(0, 5)} tone="blue" detailKey="detail"/></article>
    </section>
  </>;
}
