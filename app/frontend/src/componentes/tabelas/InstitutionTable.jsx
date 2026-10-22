import EmptyState from "../ui/EmptyState.jsx";

export default function InstitutionTable({ items, onSelect }) {
  if (!items.length) return <EmptyState message="Nenhuma instituição encontrada." />;
  return (
    <div className="data-table-wrap"><table><thead><tr><th>INSTITUIÇÃO</th><th>SIGLA</th><th>CEP</th><th>PERFIL</th></tr></thead><tbody>
      {items.map((institution) => <tr key={institution.id}>
        <td><span className="person-avatar">{(institution.sigla || institution.nome || "?").slice(0, 2).toUpperCase()}</span><strong>{institution.nome || "Nome não informado"}</strong></td>
        <td>{institution.sigla || "—"}</td><td>{institution.cep || "—"}</td>
        <td><button className="institution-open" onClick={() => onSelect(institution)}>Ver perfil →</button></td>
      </tr>)}
    </tbody></table></div>
  );
}
