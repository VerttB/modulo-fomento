import { ChevronRight } from "lucide-react";
import EmptyState from "../ui/EmptyState.jsx";
import { institutionInitials, institutionLogo } from "../../utils/institutionLogo.js";

export default function InstitutionTable({ items, onSelect }) {
  if (!items.length) return <EmptyState message="Nenhuma instituição encontrada." />;
  return (
    <div className="data-table-wrap"><table><thead><tr><th>INSTITUIÇÃO</th><th>SIGLA</th><th>CEP</th><th>PERFIL</th></tr></thead><tbody>
      {items.map((institution) => {
        const logo = institutionLogo(institution);
        return <tr key={institution.id}>
          <td>{logo
            ? <img className="institution-logo" src={logo} alt="" />
            : <span className="person-avatar">{institutionInitials(institution)}</span>}<strong>{institution.nome || "Nome não informado"}</strong></td>
          <td>{institution.sigla || "—"}</td><td>{institution.cep || "—"}</td>
          <td><button className="institution-open" onClick={() => onSelect(institution)}>Ver perfil <ChevronRight size={14} aria-hidden="true" /></button></td>
        </tr>;
      })}
    </tbody></table></div>
  );
}
