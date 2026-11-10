import { formatNumber } from "../../utils/format";
import { OriginFooter, TruncationNotice } from "./BlockNotices.jsx";
import ExternalLink from "./ExternalLink.jsx";
import ResearcherAvatar from "./ResearcherAvatar.jsx";
import { EvidenceSummary, RankingNotice } from "./ResearcherEvidence.jsx";

const METRICS = [
  ["articles", "Artigos"],
  ["books", "Livros"],
  ["book_chapters", "Capítulos"],
  ["patents", "Patentes"],
  ["software", "Softwares"],
  ["h_index", "Índice h"],
  ["citations", "Citações"],
];

const ORCID_PATTERN = /\d{4}-\d{4}-\d{4}-\d{3}[\dX]/i;

function orcidUrl(orcid) {
  const match = orcid?.match(ORCID_PATTERN);
  return match ? `https://orcid.org/${match[0].toUpperCase()}` : null;
}

function lattesUrl(lattesId) {
  const id = lattesId?.trim();
  return id ? `https://lattes.cnpq.br/${encodeURIComponent(id)}` : null;
}

function ResearcherCard({ researcher }) {
  const { name, lattes_id: lattesId, orcid, territory, city, state, abstract, evidence } = researcher;
  const metrics = researcher.metrics || {};
  const location = [city, state].filter(Boolean).join(" - ");
  const institutions = [...new Set((researcher.affiliations || [])
    .map((affiliation) => affiliation.institution_acronym || affiliation.institution_name)
    .filter(Boolean))];
  const shownMetrics = METRICS.filter(([key]) => Number(metrics[key]) > 0);
  const lattes = lattesUrl(lattesId);
  const orcidLink = orcidUrl(orcid);

  return <article className="maria-card">
    <header className="maria-card-header">
      <ResearcherAvatar lattesId={lattesId} />
      <div className="maria-card-heading">
        <h5 className="maria-card-title">{name}</h5>
        {(lattes || orcidLink) && <div className="maria-card-links">
          {lattes && <ExternalLink href={lattes}>Currículo Lattes</ExternalLink>}
          {orcidLink && <ExternalLink href={orcidLink}>ORCID</ExternalLink>}
        </div>}
      </div>
    </header>
    {(territory || location || institutions.length > 0) && <div className="maria-badges">
      {territory && <span className="maria-badge maria-badge-accent">{territory}</span>}
      {location && <span className="maria-badge">{location}</span>}
      {institutions.map((institution) => <span className="maria-badge" key={institution}>{institution}</span>)}
    </div>}
    {abstract && <p className="maria-card-abstract" title={abstract}>{abstract}</p>}
    {shownMetrics.length > 0 && <dl className="maria-card-metrics">
      {shownMetrics.map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{formatNumber(metrics[key])}</dd></div>)}
    </dl>}
    <EvidenceSummary evidence={evidence} />
  </article>;
}

export default function ResearcherCards({ block }) {
  const researchers = block.researchers || [];
  const total = block.total || researchers.length;
  return <section className="maria-data maria-cards-block">
    <h4>{block.title || "Pesquisadores"}</h4>
    <RankingNotice ranking={block.ranking} shown={researchers.length} total={total} />
    {researchers.length === 0
      ? <p>Nenhum pesquisador encontrado.</p>
      : <div className="maria-cards">{researchers.map((researcher, index) => <ResearcherCard key={researcher.id || index} researcher={researcher} />)}</div>}
    <TruncationNotice truncated={block.truncated} />
    <OriginFooter origin={block.origin} />
  </section>;
}
