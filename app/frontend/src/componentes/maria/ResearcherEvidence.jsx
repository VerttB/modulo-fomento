import { formatDate, formatNumber } from "../../utils/format";

const EVIDENCE_TYPES = {
  ARTICLE: ["artigo", "artigos"],
  BOOK: ["livro", "livros"],
  BOOK_CHAPTER: ["capítulo", "capítulos"],
  PATENT: ["patente", "patentes"],
  SOFTWARE: ["software", "softwares"],
  PARTICIPATION_EVENT: ["evento", "eventos"],
  AREA_SPECIALTY: ["área de atuação", "áreas de atuação"],
};

function evidenceLabel(type, count = 1) {
  const labels = EVIDENCE_TYPES[type];
  if (!labels) return String(type).toLowerCase();
  return count === 1 ? labels[0] : labels[1];
}

function plural(count, singular, pluralForm) {
  return `${formatNumber(count)} ${count === 1 ? singular : pluralForm}`;
}

// Explica a ordem quando a lista é um ranking por relevância.
export function RankingNotice({ ranking, shown, total }) {
  if (!ranking) return null;
  const found = plural(total, "pesquisador encontrado", "pesquisadores encontrados");
  const top = shown === 1 ? "o mais relevante" : `os ${formatNumber(shown)} mais relevantes`;
  const scope = total > shown ? `${top} de ${found}` : found;
  const dataAsOf = ranking.data_as_of ? formatDate(ranking.data_as_of) : null;
  return <div className="maria-ranking-notice" role="note">
    <strong>Ordenados por relevância de “{ranking.term}”: {scope}.</strong>
    {ranking.fields?.length > 0 && <p>A ordem considera só estes campos: {ranking.fields.join("; ")}.</p>}
    <p>Qualis, citações e índice h não entram na ordem.{dataAsOf && ` Dados de ${dataAsOf}.`}</p>
  </div>;
}

export function EvidenceSummary({ evidence }) {
  if (!evidence) return null;
  const total = evidence.total || 0;
  let summary = "Nenhuma produção sobre o tema: aparece pelo resumo do currículo.";
  if (total > 0) {
    const parts = Object.entries(evidence.by_type || {})
      .sort((a, b) => b[1] - a[1])
      .map(([type, count]) => plural(count, evidenceLabel(type, 1), evidenceLabel(type, 2)));
    summary = plural(total, "produção sobre o tema", "produções sobre o tema");
    if (parts.length > 1) summary += ` (${parts.join(", ")})`;
  }
  const items = evidence.items || [];
  return <div className="maria-card-evidence">
    <span>{summary}</span>
    {items.length > 0 && <ul>
      {items.map((item, index) => <li key={index}>
        {item.type === "PROFILE"
          ? <span className="maria-badge maria-badge-accent">Resumo do currículo</span>
          : <><span className="maria-badge">{evidenceLabel(item.type)}</span> {item.title || "Sem título"}{item.year && <span className="maria-muted"> · {item.year}</span>}</>}
      </li>)}
    </ul>}
  </div>;
}
