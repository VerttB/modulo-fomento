import EmptyState from "../componentes/ui/EmptyState.jsx";
import Pagination from "../componentes/ui/Pagination.jsx";
import PanelHeader from "../componentes/ui/PanelHeader.jsx";
import ResearcherTable from "../componentes/tabelas/ResearcherTable.jsx";
import ProjectList from "../componentes/tabelas/ProjectList.jsx";
import ScholarshipTable from "../componentes/tabelas/ScholarshipTable.jsx";
import InstitutionTable from "../componentes/tabelas/InstitutionTable.jsx";

const directoryConfig = {
  instituicoes: { title: "Instituições", subtitle: "Selecione uma instituição para explorar seu perfil de fomento." },
  pesquisadores: { title: "Pesquisadores", subtitle: "Registros paginados da API" },
  projetos: { title: "Projetos", subtitle: "Registros paginados da API" },
  bolsas: { title: "Bolsistas", subtitle: "Registros, situação e conflitos no recorte filtrado." },
};

const directoryTable = {
  instituicoes: InstitutionTable,
  pesquisadores: ResearcherTable,
  projetos: ProjectList,
  bolsas: ScholarshipTable,
};

export default function DirectoryPage({ view, data, state, error, onRetry, onPageChange, onSelectInstitution }) {
  const config = directoryConfig[view];
  const Table = directoryTable[view];
  return (
    <article className="panel table-panel">
      <PanelHeader title={config.title} subtitle={config.subtitle} action="" />
      {state === "loading" ? <EmptyState message={`Carregando ${config.title.toLowerCase()}…`} />
        : state === "error" ? <div className="api-error" role="alert"><span>{error}</span><button onClick={onRetry}>Tentar novamente</button></div>
          : <><Table items={data?.items || []} onSelect={onSelectInstitution} />{data && <Pagination page={data.page} pages={data.pages} total={data.total} onChange={onPageChange} />}</>}
    </article>
  );
}
