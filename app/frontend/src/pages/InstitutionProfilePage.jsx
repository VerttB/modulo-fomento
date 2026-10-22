import { useEffect, useState } from "react";
import {
  getInstitutionProfile,
  getInstitutionResearchers,
  getInstitutionProjects,
  getInstitutionScholarships,
} from "../services/instituicoes.ts";
import { getErrorMessage } from "../services/http.ts";
import BarList from "../componentes/graficos/BarList.jsx";
import PopulationRateList from "../componentes/graficos/PopulationRateList.jsx";
import TrendChart from "../componentes/graficos/TrendChart.jsx";
import InstitutionScholarshipTable from "../componentes/tabelas/InstitutionScholarshipTable.jsx";
import ResearcherTable from "../componentes/tabelas/ResearcherTable.jsx";
import ProjectList from "../componentes/tabelas/ProjectList.jsx";
import EmptyState from "../componentes/ui/EmptyState.jsx";
import MetricCard from "../componentes/ui/MetricCard.jsx";
import Pagination from "../componentes/ui/Pagination.jsx";
import PanelHeader from "../componentes/ui/PanelHeader.jsx";
import { formatNumber } from "../utils/format.js";

const tabs = [
  ["resumo", "Resumo"],
  ["pesquisadores", "Pesquisadores"],
  ["projetos", "Projetos"],
  ["bolsas", "Bolsas"],
];

export default function InstitutionProfilePage({ institution, onBack, onApiStateChange }) {
  const [profile, setProfile] = useState(null);
  const [profileState, setProfileState] = useState("loading");
  const [profileError, setProfileError] = useState("");
  const [profileRetry, setProfileRetry] = useState(0);
  const [tab, setTab] = useState("resumo");
  const [page, setPage] = useState(1);
  const [pageData, setPageData] = useState(null);
  const [pageState, setPageState] = useState("loading");
  const [pageError, setPageError] = useState("");
  const [pageRetry, setPageRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setProfileState("loading");
    setProfileError("");
    getInstitutionProfile(institution.id, controller.signal)
      .then((data) => { setProfile(data); setProfileState("ready"); })
      .catch((error) => {
        if (error.name !== "AbortError") {
          setProfileError(getErrorMessage(error));
          setProfileState("error");
        }
      });
    return () => controller.abort();
  }, [institution.id, profileRetry]);

  useEffect(() => onApiStateChange?.(profileState), [profileState, onApiStateChange]);

  useEffect(() => {
    if (tab === "resumo" || !institution?.id) return;
    const controller = new AbortController();
    const loaders = {
      pesquisadores: getInstitutionResearchers,
      projetos: getInstitutionProjects,
      bolsas: getInstitutionScholarships,
    };
    setPageState("loading");
    setPageError("");
    loaders[tab](institution.id, page, 20, controller.signal)
      .then((data) => { setPageData(data); setPageState("ready"); })
      .catch((error) => {
        if (error.name !== "AbortError") {
          setPageError(getErrorMessage(error));
          setPageState("error");
        }
      });
    return () => controller.abort();
  }, [institution.id, tab, page, pageRetry]);

  function selectTab(nextTab) {
    setTab(nextTab);
    setPage(1);
  }

  if (profileState === "loading") return <section className="panel"><EmptyState message="Carregando perfil da instituição…" /></section>;
  if (profileState === "error") return <div className="api-error" role="alert"><span>{profileError}</span><button onClick={() => setProfileRetry((value) => value + 1)}>Tentar novamente</button></div>;
  if (!profile) return null;

  const report = profile.estatisticas;
  const modalities = Object.entries(report.por_modalidade || {}).map(([label, total]) => ({ label, total }));
  const areas = (report.por_area || []).map((item) => ({ label: item.area, total: item.total }));
  const dataTable = tab === "pesquisadores" ? <ResearcherTable items={pageData?.items || []} />
    : tab === "projetos" ? <ProjectList items={pageData?.items || []} />
      : <InstitutionScholarshipTable items={pageData?.items || []} />;

  return <section className="institution-profile">
    <button className="back-link" onClick={onBack}>← Voltar para instituições</button>
    <section className="metric-grid institution-metrics">
      <MetricCard label="Bolsas" value={formatNumber(report.total)} hint="no período e filtros da base" icon="▤" accent="teal" />
      <MetricCard label="Pesquisadores" value={formatNumber(profile.total_pesquisadores)} hint="vinculados a bolsas da instituição" icon="♙" accent="violet" />
      <MetricCard label="Projetos" value={formatNumber(profile.total_projetos)} hint="com bolsas associadas" icon="◇" accent="orange" />
      <MetricCard label="Municípios" value={formatNumber(report.por_cidade?.length || 0)} hint="de origem dos pesquisadores" icon="⌖" accent="blue" />
    </section>

    <div className="institution-tabs" role="tablist" aria-label="Dados da instituição">
      {tabs.map(([id, label]) => <button key={id} role="tab" aria-selected={tab === id} className={tab === id ? "active" : ""} onClick={() => selectTab(id)}>{label}{id === "pesquisadores" ? ` · ${formatNumber(profile.total_pesquisadores)}` : id === "projetos" ? ` · ${formatNumber(profile.total_projetos)}` : id === "bolsas" ? ` · ${formatNumber(report.total)}` : ""}</button>)}
    </div>

    {tab === "resumo" ? <>
      <section className="analytics-grid">
        <article className="panel"><PanelHeader title="Evolução das bolsas" subtitle="Quantidade por ano de início" action="" /><TrendChart values={report.por_ano || []} /></article>
        <article className="panel"><PanelHeader title="Modalidades" subtitle="Distribuição do apoio" action="" /><BarList items={modalities.slice(0, 8)} tone="teal" /></article>
      </section>
      <section className="analytics-grid">
        <article className="panel"><PanelHeader title="Áreas do conhecimento" subtitle="Projetos apoiados pela instituição" action="" /><BarList items={areas.slice(0, 8)} tone="violet" /></article>
        <article className="panel"><PanelHeader title="Municípios por taxa populacional" subtitle="Bolsas a cada 10 mil habitantes" action="" /><PopulationRateList items={report.por_cidade} labelKey="cidade" /></article>
      </section>
      <section className="panel full-panel"><PanelHeader title="Territórios de identidade" subtitle="Bolsas a cada 10 mil habitantes do território" action="" /><PopulationRateList items={report.por_territorio_identidade} labelKey="territorio_identidade" /></section>
    </> : <article className="panel table-panel">
      <PanelHeader title={tabs.find(([id]) => id === tab)?.[1]} subtitle={`${institution.nome || "Instituição"}${institution.sigla ? ` · ${institution.sigla}` : ""}`} action="" />
      {pageState === "loading" ? <EmptyState message="Carregando registros…" />
        : pageState === "error" ? <div className="api-error" role="alert"><span>{pageError}</span><button onClick={() => setPageRetry((value) => value + 1)}>Tentar novamente</button></div>
          : <>{dataTable}{pageData && <Pagination page={pageData.page} pages={pageData.pages} total={pageData.total} onChange={setPage} />}</>}
    </article>}
  </section>;
}
