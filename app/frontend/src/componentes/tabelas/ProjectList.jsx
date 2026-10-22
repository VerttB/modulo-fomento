import EmptyState from "../ui/EmptyState.jsx";

export default function ProjectList({ items }) {
  if (!items.length) return <EmptyState message="Nenhum projeto retornado pela API." />;
  return (
    <div className="project-list">
      {items.map((project, index) => <article className="project-row" key={project.id}>
        <span className="project-number">{String(index + 1).padStart(2, "0")}</span>
        <div><strong>{project.nome || "Projeto sem título"}</strong><small>{project.area_conhecimento?.termo || "Área não informada"}</small><p>{project.resumo || "Sem resumo cadastrado."}</p></div>
        <span className="project-type">{project.area_conhecimento?.tipo || "—"}</span>
      </article>)}
    </div>
  );
}
