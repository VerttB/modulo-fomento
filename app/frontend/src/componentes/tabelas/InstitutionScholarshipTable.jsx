import EmptyState from "../ui/EmptyState.jsx";

export default function InstitutionScholarshipTable({ items }) {
  if (!items.length) return <EmptyState message="Nenhuma bolsa encontrada para esta instituição." />;
  return <div className="data-table-wrap"><table><thead><tr>
    <th>PESQUISADOR(A)</th><th>PROJETO</th><th>MODALIDADE</th><th>INÍCIO</th><th>FIM</th><th>STATUS</th>
  </tr></thead><tbody>{items.map((item) => <tr key={item.id}>
    <td><strong>{item.pesquisador_nome || "Nome não informado"}</strong><small className="table-secondary">{[item.pesquisador_cidade, item.nome_curso].filter(Boolean).join(" · ")}</small></td>
    <td>{item.projeto_nome || "—"}</td><td>{item.modalidade || "—"}</td>
    <td>{item.quando_iniciou || "—"}</td><td>{item.quando_terminou || "—"}</td>
    <td><span className={`tag status-${(item.status || "").toLowerCase()}`}>{item.is_conflict ? "Em revisão" : item.status || "—"}</span></td>
  </tr>)}</tbody></table></div>;
}
