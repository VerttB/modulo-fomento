import { OriginFooter, TruncationNotice } from "./BlockNotices.jsx";
import ExternalLink from "./ExternalLink.jsx";

const MAX_AUTHORS = 8;
const DOI_PREFIX = /^(?:https?:\/\/(?:dx\.)?doi\.org\/|doi:\s*)/i;

function doiUrl(doi) {
  const value = doi?.trim().replace(DOI_PREFIX, "");
  return value?.startsWith("10.") ? `https://doi.org/${encodeURI(value)}` : null;
}

function authorsText(authors) {
  const names = (authors || []).map((author) => author.name).filter(Boolean);
  if (names.length <= MAX_AUTHORS) return names.join(", ");
  const rest = names.length - MAX_AUTHORS;
  return `${names.slice(0, MAX_AUTHORS).join(", ")} e mais ${rest} ${rest === 1 ? "autor" : "autores"}`;
}

function ProductionCard({ production }) {
  const details = production.details || {};
  const authors = authorsText(production.authors);
  const doi = doiUrl(details.doi);
  const facts = [
    ["Periódico", details.magazine],
    ["Evento", details.event_name],
    ["Situação", details.status],
    ["ISBN", details.isbn],
    ["ISSN", details.issn],
  ].filter(([, value]) => value);

  return <article className="maria-card">
    <h5 className="maria-card-title">{production.title}</h5>
    <div className="maria-badges">
      <span className="maria-badge maria-badge-accent">{production.type_label || production.type}</span>
      {production.year && <span className="maria-badge">{production.year}</span>}
      {details.qualis && <span className="maria-badge">Qualis {details.qualis}</span>}
    </div>
    {authors && <p className="maria-card-authors">Autores: {authors}</p>}
    {(facts.length > 0 || doi) && <dl className="maria-card-facts">
      {facts.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
      {doi && <div><dt>DOI</dt><dd><ExternalLink href={doi}>{details.doi}</ExternalLink></dd></div>}
    </dl>}
  </article>;
}

export default function ProductionCards({ block }) {
  const productions = block.productions || [];
  return <section className="maria-data maria-cards-block">
    <h4>{block.title || "Produções científicas e tecnológicas"}</h4>
    {productions.length === 0
      ? <p>Nenhuma produção encontrada.</p>
      : <div className="maria-cards">{productions.map((production, index) => <ProductionCard key={production.id || index} production={production} />)}</div>}
    <TruncationNotice truncated={block.truncated} />
    <OriginFooter origin={block.origin} />
  </section>;
}
