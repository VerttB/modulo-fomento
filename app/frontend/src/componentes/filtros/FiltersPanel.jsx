import FilterSelect from "../ui/FilterSelect.jsx";
import { formatNumber } from "../../utils/format.js";

export default function FiltersPanel({ filters, choices, onChange, onReset }) {
  const years = (choices.years || []).map((year) => ({ value: year, label: year }));
  const options = (items, label) => [{ value: "", label }, ...items.map((item) => ({ value: item, label: item }))];
  const cities = [{ value: "", label: "Todos" }, ...(choices.cityRows || []).map((item) => ({
    value: item.cidade,
    label: item.populacao_estimada
      ? `${item.cidade} · ${formatNumber(item.populacao_estimada)} hab.`
      : item.cidade,
  }))];

  return (
    <section className="filterbar" aria-label="Filtros dos dados">
      <div className="filter-heading"><span className="filter-glyph">☷</span><strong>Filtros</strong><button onClick={onReset}>Limpar</button></div>
      <FilterSelect label="De" value={filters.from} onChange={(value) => onChange("from", value)} options={options(years.map((item) => item.value), "Todos")} />
      <FilterSelect label="Até" value={filters.to} onChange={(value) => onChange("to", value)} options={options(years.map((item) => item.value).sort(), "Todos")} />
      <FilterSelect label="Modalidade" value={filters.modality} onChange={(value) => onChange("modality", value)} options={options(choices.modalities || [], "Todas")} />
      <FilterSelect label="Município" value={filters.city} onChange={(value) => onChange("city", value)} options={cities} />
      <FilterSelect label="Instituição" value={filters.institution} onChange={(value) => onChange("institution", value)} options={options(choices.institutions || [], "Todas")} />
      <FilterSelect label="Área" value={filters.area} onChange={(value) => onChange("area", value)} options={options(choices.areas || [], "Todas")} />
      <FilterSelect label="Grande área" value={filters.largeArea} onChange={(value) => onChange("largeArea", value)} options={options(choices.largeAreas || [], "Todas")} />
      <FilterSelect label="Território" value={filters.territory} onChange={(value) => onChange("territory", value)} options={options(choices.territories || [], "Todos")} />
    </section>
  );
}
