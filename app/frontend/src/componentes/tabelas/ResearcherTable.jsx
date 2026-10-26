import EmptyState from "../ui/EmptyState.jsx";

export default function ResearcherTable({ items }) {
  if (!items.length) return <EmptyState message="Nenhum pesquisador retornado pela API." />;
  return (
    <>
      <div className="data-table-wrap"><table><thead><tr><th>PESQUISADOR(A)</th><th>CIDADE</th><th>CEP DO ÚLTIMO VÍNCULO</th><th>TERRITÓRIO</th><th>STATUS</th></tr></thead><tbody>
        {items.map((person) => <tr key={person.id}><td><span className="person-avatar">{initials(person.nome)}</span><strong>{person.nome || "Nome não informado"}</strong></td><td>{person.cidade || "—"}</td><td>{person.cep_referencia || "—"}</td><td>{person.territorio_identidade?.nome || "—"}</td><td><span className={`tag status-${(person.status || "").toLowerCase()}`}>{person.status || "—"}</span></td></tr>)}
      </tbody></table></div>
      <p className="location-note">Cidade baseada no CEP do vínculo mais recente: unidade, departamento e, se necessário, instituição.</p>
    </>
  );
}

function initials(name) {
  return name?.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase() || "?";
}
