import { useCallback, useEffect, useMemo, useState } from "react";
import { exportScholarshipSummary, exportScholarships, getScholarshipPage, getStatistics } from "./services/bolsas";
import { getErrorMessage } from "./services/http";
import { getResearchersPage } from "./services/pesquisadores";
import { getProjectsPage } from "./services/projetos";
import { getInstitutionsPage } from "./services/instituicoes";
import { getCities, synchronizeResearcherTerritories } from "./services/territorios";
import FiltersPanel from "./componentes/filtros/FiltersPanel.jsx";
import SummaryExportMenu from "./componentes/exportacao/SummaryExportMenu.jsx";
import IngestionsPanel from "./componentes/ingestoes/IngestionsPanel.jsx";
import EmptyState from "./componentes/ui/EmptyState.jsx";
import DirectoryPage from "./pages/DirectoryPage.jsx";
import GuidedSearchPage from "./pages/GuidedSearchPage.jsx";
import IndicatorsPage from "./pages/IndicatorsPage.jsx";
import PanoramaPage from "./pages/PanoramaPage.jsx";
import TerritoriesPage from "./pages/TerritoriesPage.jsx";
import InstitutionProfilePage from "./pages/InstitutionProfilePage.jsx";
import { formatNumber, normalizeText } from "./utils/format.js";

const navigation = [
  ["panorama", "Panorama", "◫"],
  ["indicadores", "Indicadores", "▥"],
  ["territorios", "Territórios", "⌖"],
  ["bolsas", "Bolsistas", "▤"],
  ["pesquisadores", "Pesquisadores", "♙"],
  ["projetos", "Projetos", "◇"],
  ["instituicoes", "Instituições", "⌂"],
  ["maria", "Consulta guiada", "✳"],
];
const initialFilters = { from: "", to: "", modality: [], city: [], institution: [], area: [], largeArea: [], territory: [] };
const labelFor = (view) => view === "ingestoes" ? "Ingestões" : navigation.find(([id]) => id === view)?.[1] || "Panorama";
const directoryViews = ["instituicoes", "pesquisadores", "projetos", "bolsas"];
const reportViews = ["panorama", "indicadores", "territorios", "maria"];
const metricRows = (items, key) => (items || []).map((item) => ({ label: item[key], total: item.total }));

export default function App() {
  const [view, setView] = useState("panorama");
  const [mobileNav, setMobileNav] = useState(false);
  const [adminExpanded, setAdminExpanded] = useState(false);
  const [filters, setFilters] = useState({ ...initialFilters });
  const [baseReport, setBaseReport] = useState(null);
  const [report, setReport] = useState(null);
  const [reportState, setReportState] = useState("loading");
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [listPage, setListPage] = useState(1);
  const [listData, setListData] = useState(null);
  const [listState, setListState] = useState("loading");
  const [listError, setListError] = useState("");
  const [exporting, setExporting] = useState(false);
  const [summaryExporting, setSummaryExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState("csv");
  const [exportError, setExportError] = useState("");
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [searchDraft, setSearchDraft] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [cities, setCities] = useState([]);
  const [citiesError, setCitiesError] = useState("");
  const [syncingTerritories, setSyncingTerritories] = useState(false);
  const [territorySyncResult, setTerritorySyncResult] = useState("");
  const [selectedInstitution, setSelectedInstitution] = useState(null);
  const [institutionProfileState, setInstitutionProfileState] = useState("loading");
  const [ingestionApiState, setIngestionApiState] = useState("loading");

  useEffect(() => {
    setSearchDraft("");
    setSearchTerm("");
  }, [view]);

  useEffect(() => {
    const controller = new AbortController();
    getStatistics(initialFilters, controller.signal).then(setBaseReport)
      .catch((cause) => { if (cause.name !== "AbortError") setBaseReport(null); });
    return () => controller.abort();
  }, [retry]);

  useEffect(() => {
    if (view !== "territorios") return;
    const controller = new AbortController();
    setCitiesError("");
    getCities(controller.signal).then(setCities)
      .catch((cause) => { if (cause.name !== "AbortError") setCitiesError(getErrorMessage(cause)); });
    return () => controller.abort();
  }, [retry, view]);

  useEffect(() => {
    if (!reportViews.includes(view)) return;
    const controller = new AbortController();
    setReportState("loading");
    setError("");
    getStatistics(filters, controller.signal)
      .then((data) => { setReport(data); setReportState("ready"); })
      .catch((cause) => {
        if (cause.name !== "AbortError") {
          setReport(null);
          setError(getErrorMessage(cause));
          setReportState("error");
        }
      });
    return () => controller.abort();
  }, [filters, retry, view]);

  useEffect(() => {
    if (!directoryViews.includes(view)) return;
    const controller = new AbortController();
    setListState("loading");
    setListError("");
    const result = view === "instituicoes"
      ? getInstitutionsPage(listPage, 10, searchTerm, controller.signal)
      : view === "bolsas"
      ? getScholarshipPage(listPage, 10, filters, controller.signal, searchTerm)
      : view === "pesquisadores"
        ? getResearchersPage(listPage, 10, searchTerm, controller.signal)
        : getProjectsPage(listPage, 10, searchTerm, controller.signal);
    result.then((data) => { setListData(data); setListState("ready"); })
      .catch((cause) => {
        if (cause.name !== "AbortError") {
          setListError(getErrorMessage(cause));
          setListState("error");
        }
      });
    return () => controller.abort();
  }, [view, listPage, filters, retry, searchTerm]);

  const choices = useMemo(() => ({
    years: (baseReport?.por_ano || []).map(({ ano }) => String(ano)).sort((a, b) => b.localeCompare(a)),
    modalities: Object.keys(baseReport?.por_modalidade || {}).sort(),
    institutions: (baseReport?.por_instituicao || []).map(({ nome, sigla }) => sigla || nome).filter(Boolean).sort(),
    areas: (baseReport?.por_area || []).map(({ area }) => area).filter(Boolean).sort(),
    largeAreas: (baseReport?.por_grande_area || []).map(({ grande_area }) => grande_area).filter(Boolean).sort(),
    territories: (baseReport?.por_territorio_identidade || []).map(({ territorio_identidade }) => territorio_identidade).filter(Boolean).sort(),
  }), [baseReport]);
  const modalityRows = useMemo(() => Object.entries(report?.por_modalidade || {})
    .map(([label, total]) => ({ label, total })).sort((a, b) => b.total - a.total), [report]);
  const institutionRows = useMemo(() => (report?.por_instituicao || []).map((item) => ({
    label: item.sigla || item.nome,
    detail: item.sigla ? item.nome : "",
    total: item.total,
  })), [report]);
  const totals = report ? {
    total: formatNumber(report.total),
    modalities: formatNumber(modalityRows.length),
    cities: formatNumber(report.por_cidade?.length || 0),
    institutions: formatNumber(report.por_instituicao?.length || 0),
  } : { total: "0", modalities: "0", cities: "0", institutions: "0" };

  const exportResults = useCallback(async () => {
    setExporting(true);
    setExportError("");
    try {
      const blob = await exportScholarships(filters, view === "bolsas" ? searchTerm : "", exportFormat);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `bolsistas-fapesb.${exportFormat}`;
      link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (cause) { setExportError(getErrorMessage(cause)); }
    finally { setExporting(false); }
  }, [exportFormat, filters, searchTerm, view]);

  const exportSummary = useCallback(async (dimensions) => {
    setSummaryExporting(true);
    setExportError("");
    try {
      const blob = await exportScholarshipSummary(filters, dimensions, exportFormat);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      const suffix = dimensions.length === 3 ? "todos" : dimensions.join("-");
      link.download = `resumo-${suffix}-bolsistas-fapesb.${exportFormat}`;
      link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      return true;
    } catch (cause) { setExportError(getErrorMessage(cause)); return false; }
    finally { setSummaryExporting(false); }
  }, [exportFormat, filters]);

  const synchronizeTerritories = useCallback(async () => {
    setSyncingTerritories(true);
    setTerritorySyncResult("");
    try {
      const result = await synchronizeResearcherTerritories();
      setTerritorySyncResult(
        `${formatNumber(result.territorios_atualizados)} territórios vinculados; ${formatNumber(result.territorios_removidos)} removidos por não haver correspondência no CSV; ${formatNumber(result.cidades_sem_correspondencia)} cidades fora da base.${result.metricas_atualizadas ? " Indicadores atualizados." : " Atenção: os indicadores não foram atualizados."}`,
      );
      setRetry((value) => value + 1);
    } catch (cause) {
      setTerritorySyncResult(`Falha ao atualizar territórios: ${getErrorMessage(cause)}`);
    } finally { setSyncingTerritories(false); }
  }, []);

  function ask(question = query) {
    if (!question.trim() || !report) return;
    setQuery(question);
    const normalized = normalizeText(question);
    const selected = [
      ...modalityRows.map((item) => ["modalidade", item.label]),
      ...(report.por_cidade || []).map((item) => ["cidade", item.cidade]),
      ...(report.por_territorio_identidade || []).map((item) => ["territorio", item.territorio_identidade]),
      ...(report.por_instituicao || []).map((item) => ["instituicao", item.sigla || item.nome]),
    ].find(([, value]) => value && normalized.includes(normalizeText(value)));
    if (selected) {
      const rows = selected[0] === "modalidade" ? modalityRows
        : selected[0] === "cidade" ? metricRows(report.por_cidade, "cidade")
          : selected[0] === "territorio" ? metricRows(report.por_territorio_identidade, "territorio_identidade")
            : institutionRows;
      const match = rows.find((item) => normalizeText(item.label) === normalizeText(selected[1]));
      setAnswer(match ? `${match.label}: ${formatNumber(match.total)} registros de bolsistas no recorte selecionado.` : "Não encontrei esse recorte entre os dados agregados disponíveis.");
      return;
    }
    setAnswer(`${formatNumber(report.total)} registros de bolsistas no recorte atual, em ${formatNumber(report.por_cidade?.length || 0)} municípios e ${formatNumber(report.por_instituicao?.length || 0)} instituições. Consulte os indicadores para detalhar por modalidade, cidade, instituição, área ou território.`);
  }

  function setFilter(key, value) {
    setListPage(1);
    setFilters((current) => ({ ...current, [key]: value }));
  }

  function resetFilters() {
    setListPage(1);
    setFilters({ ...initialFilters });
  }

  const currentApiState = view === "instituicao-perfil" ? institutionProfileState
    : view === "ingestoes" ? ingestionApiState
    : directoryViews.includes(view) ? listState : reportState;
  const canExport = view === "bolsas" ? listState === "ready" : reportState === "ready";

  return (
    <div className={`app-shell view-${view} min-h-screen bg-app text-ink font-sans`}>
      <aside className={`sidebar ${mobileNav ? "sidebar-open" : ""}`}>
        <a className="brand" href="#panorama" onClick={() => setView("panorama")}><span className="brand-mark"><span>O</span></span><span><strong>observa<span className="brand-light">tório</span></strong><small>FAPESB · BAHIA</small></span></a>
        <div className="side-caption">EXPLORAR</div>
        <nav className="side-nav" aria-label="Navegação principal">
          {navigation.map(([id, label, icon]) => <button key={id} className={`nav-item ${view === id || (id === "instituicoes" && view === "instituicao-perfil") ? "active" : ""}`} onClick={() => { setView(id); setMobileNav(false); }}><span className="nav-icon">{icon}</span>{label}</button>)}
          <button
            className={`nav-item admin-nav-toggle ${view === "ingestoes" ? "active" : ""}`}
            aria-expanded={adminExpanded}
            onClick={() => setAdminExpanded((expanded) => !expanded)}
          >
            <span className="nav-icon">⚙</span>Administração
            <span className="nav-chevron" aria-hidden="true">{adminExpanded ? "⌄" : "›"}</span>
          </button>
          {adminExpanded && (
            <div className="nav-submenu">
              <button className={`nav-subitem ${view === "ingestoes" ? "active" : ""}`} onClick={() => { setView("ingestoes"); setAdminExpanded(true); setMobileNav(false); }}>
                <span aria-hidden="true">⇧</span>Ingestões
              </button>
            </div>
          )}
        </nav>
        <div className="sidebar-bottom"><div className="fapesb-stamp"><span className="seal">✳</span><span><strong>FAPESB</strong><small>Fundação de Amparo à Pesquisa<br />do Estado da Bahia</small></span></div><div className="side-footer">Observatório de Bolsistas <span>v1.0</span></div></div>
      </aside>
      <main className="main-area">
        <header className="topbar"><button className="mobile-menu" onClick={() => setMobileNav((open) => !open)} aria-label="Abrir menu">☰</button><div className="breadcrumbs">Observatório <span>/</span> <strong>{view === "instituicao-perfil" ? "Instituições" : labelFor(view)}</strong></div><div className="topbar-right"><span className={`source-status ${currentApiState === "ready" ? "is-live" : ""}`}><i />{currentApiState === "ready" ? "API conectada" : currentApiState === "loading" ? "Consultando API" : "API indisponível"}</span><button className="avatar" aria-label="Perfil">OB</button></div></header>
        <div className="page-content">
          <div className="page-heading"><div><div className="eyebrow">CIÊNCIA, PESSOAS E TERRITÓRIOS</div><h1>{view === "instituicao-perfil" ? selectedInstitution?.nome || "Perfil da instituição" : view === "maria" ? "Explore os dados" : view === "panorama" ? "Panorama de bolsistas" : labelFor(view)}</h1><p>{view === "instituicao-perfil" ? [selectedInstitution?.sigla, selectedInstitution?.cep].filter(Boolean).join(" · ") || "Dados específicos de fomento" : "Fomento à formação científica nos territórios da Bahia"}</p></div>{view !== "ingestoes" && !["pesquisadores", "projetos", "instituicoes", "instituicao-perfil"].includes(view) && <div className="heading-actions"><label className="export-format"><span>Formato</span><select value={exportFormat} onChange={(event) => setExportFormat(event.target.value)} aria-label="Formato da exportação"><option value="csv">CSV</option><option value="xlsx">Excel (.xlsx)</option></select></label><button className="export-button" disabled={!canExport || exporting} aria-busy={exporting} onClick={exportResults}>{exporting ? <><span className="export-spinner" aria-hidden="true" />Preparando…</> : <><span>↓</span> Exportar registros</>}</button><SummaryExportMenu disabled={!canExport} loading={summaryExporting} format={exportFormat} onExport={exportSummary} /></div>}</div>
          {directoryViews.includes(view) && <form className="search-toolbar" onSubmit={(event) => { event.preventDefault(); setListPage(1); setSearchTerm(searchDraft.trim()); }}>
          <span aria-hidden="true">⌕</span><input value={searchDraft} onChange={(event) => setSearchDraft(event.target.value)} placeholder={view === "projetos" ? 'Buscar título, resumo ou área… (AND, OR, NOT)' : view === "bolsas" ? "Buscar pessoa, projeto, instituição, modalidade ou cidade…" : view === "instituicoes" ? "Buscar instituição por nome ou sigla…" : "Buscar por nome, cidade ou Lattes…"} aria-label="Buscar registros" />
            <button type="submit">Buscar</button>{(searchTerm || searchDraft) && <button type="button" className="search-clear" onClick={() => { setSearchDraft(""); setSearchTerm(""); setListPage(1); }}>Limpar</button>}
          </form>}
          {(reportViews.includes(view) || view === "bolsas") && <FiltersPanel filters={filters} choices={{ ...choices, cityRows: baseReport?.por_cidade || [] }} onChange={setFilter} onReset={resetFilters} />}
          {reportState === "error" && reportViews.includes(view) && <div className="api-error" role="alert"><span>{error}</span><button onClick={() => setRetry((value) => value + 1)}>Tentar novamente</button></div>}
          {exportError && <div className="api-error" role="alert"><span>Não foi possível exportar: {exportError}</span><button onClick={() => setExportError("")}>Fechar</button></div>}
          {view === "ingestoes" ? <IngestionsPanel onApiStateChange={setIngestionApiState} />
            : view === "instituicao-perfil" ? selectedInstitution ? <><InstitutionProfilePage institution={selectedInstitution} onBack={() => setView("instituicoes")} onApiStateChange={setInstitutionProfileState} /><PageFooter /></> : <section className="panel"><EmptyState message="Selecione uma instituição na lista para abrir seu perfil." /></section>
              : directoryViews.includes(view) ? <><DirectoryPage view={view} data={listData} state={listState} error={listError} onRetry={() => setRetry((value) => value + 1)} onPageChange={setListPage} onSelectInstitution={(institution) => { setSelectedInstitution(institution); setView("instituicao-perfil"); }} /><PageFooter /></>
              : view === "maria" ? <GuidedSearchPage query={query} answer={answer} onChange={setQuery} onSubmit={ask} total={report?.total || 0} disabled={reportState !== "ready"} />
                : reportState === "loading" ? <section className="panel"><EmptyState message="Consultando os dados da API…" /></section>
                  : reportState === "error" ? null : <>
                    {view === "panorama" && <PanoramaPage report={report} totals={totals} modalityRows={modalityRows} institutionRows={institutionRows} filters={filters} onNavigate={setView} />}
                    {view === "indicadores" && <IndicatorsPage report={report} />}
                    {view === "territorios" && <TerritoriesPage report={report} cities={cities} citiesError={citiesError} onRetry={() => setRetry((value) => value + 1)} onSynchronize={synchronizeTerritories} syncing={syncingTerritories} syncResult={territorySyncResult} />}
                    <PageFooter />
                  </>}
        </div>
      </main>
    </div>
  );
}

function PageFooter() {
  return <footer className="page-footer"><span>Indicadores e registros consultados na API v1.</span><span>Fundação de Amparo à Pesquisa do Estado da Bahia <b>·</b> FAPESB</span></footer>;
}
