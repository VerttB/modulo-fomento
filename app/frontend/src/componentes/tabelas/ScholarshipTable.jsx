import EmptyState from "../ui/EmptyState.jsx";

export default function ScholarshipTable({ items }) {
  if (!items.length) return <EmptyState message="Nenhum registro de bolsista encontrado para os filtros selecionados." />;
  return (
    <div className="data-table-wrap"><table><thead><tr>
      <th>INÍCIO</th><th>MODALIDADE</th><th>CURSO</th><th>CEP DE REFERÊNCIA</th><th>STATUS</th><th>CONFLITO</th>
    </tr></thead><tbody>{items.map((item) => <tr key={item.id}>
      <td>{item.quando_iniciou || "—"}</td><td>{item.modalidade || "—"}</td><td>{item.nome_curso || "—"}</td>
      <td>{item.cep_referencia || "—"}</td><td><span className={`tag status-${(item.status || "").toLowerCase()}`}>{item.status || "—"}</span></td>
      <td>{item.is_conflict ? <span className="tag status-conflito">Em revisão</span> : "Não"}</td>
    </tr>)}</tbody></table></div>
  );
}
