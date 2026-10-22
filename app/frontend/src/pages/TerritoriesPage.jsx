import MapaCidades from "../componentes/mapa/MapaCidades.jsx";
import BarList from "../componentes/graficos/BarList.jsx";
import PanelHeader from "../componentes/ui/PanelHeader.jsx";
import { formatNumber } from "../utils/format.js";

const rows = (items, key) => (items || []).map((item) => ({ label: item[key], total: item.total }));

export default function TerritoriesPage({ report, cities, citiesError, onRetry, onSynchronize, syncing, syncResult }) {
  const cityRows = (report.por_cidade || []).slice(0, 10).map((item) => ({
    label: item.cidade,
    detail: item.populacao_estimada
      ? `${formatNumber(item.populacao_estimada)} habitantes · ${formatNumber(item.bolsas_por_100_mil_habitantes)} bolsas/100 mil hab.`
      : "População não encontrada na base municipal",
    total: item.total,
  }));

  return <>
    {citiesError
      ? <div className="api-error" role="alert"><span>Não foi possível carregar os municípios: {citiesError}</span><button onClick={onRetry}>Tentar novamente</button></div>
      : <MapaCidades cidades={cities} bolsasPorCidade={report.por_cidade || []} onSynchronizeTerritories={onSynchronize} syncingTerritories={syncing} syncResult={syncResult}/>}
    <section className="analytics-grid lower-grid">
      <article className="panel"><PanelHeader title="Territórios de identidade" subtitle="Bolsas por território no recorte" action=""/><BarList items={rows(report.por_territorio_identidade, "territorio_identidade").slice(0, 15)} tone="teal" emptyMessage="Nenhum território retornado pela API."/></article>
      <article className="panel"><PanelHeader title="Municípios" subtitle="Bolsas e população estimada" action=""/><BarList items={cityRows} tone="teal" detailKey="detail"/></article>
    </section>
  </>;
}
