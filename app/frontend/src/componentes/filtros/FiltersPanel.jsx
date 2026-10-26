import FilterSelect from "../ui/FilterSelect.jsx";
import FilterMultiSelect from "../ui/FilterMultiSelect.jsx";
import { formatNumber } from "../../utils/format.js";

export default function FiltersPanel({ filters, choices, onChange, onReset }) {
  const years = (choices.years || []).map((year) => ({ value: year, label: year }));
  const options = (items, label) => [{ value: "", label }, ...items.map((item) => ({ value: item, label: item }))];
  const cities = (choices.cityRows || []).map((item) => ({
    value: item.cidade,
    label: item.populacao_estimada
      ? `${item.cidade} · ${formatNumber(item.populacao_estimada)} hab.`
      : item.cidade,
  }));
  const multiOptions = (items) => (items || []).map((item) => ({ value: item, label: item }));

  return (
    <section className="filterbar" aria-label="Filtros dos dados">
      <div className="filter-heading"><span className="filter-glyph">☷</span><strong>Filtros</strong><button onClick={onReset}>Limpar</button></div>
      <FilterSelect label="De" value={filters.from} onChange={(value) => onChange("from", value)} options={options(years.map((item) => item.value), "Todos")} />
      <FilterSelect label="Até" value={filters.to} onChange={(value) => onChange("to", value)} options={options(years.map((item) => item.value).sort(), "Todos")} />
      <FilterMultiSelect label="Modalidade" values={filters.modality} onChange={(value) => onChange("modality", value)} options={multiOptions(choices.modalities)} allLabel="Todas" />
      <FilterMultiSelect label="Município" values={filters.city} onChange={(value) => onChange("city", value)} options={cities} />
      <FilterMultiSelect label="Instituição" values={filters.institution} onChange={(value) => onChange("institution", value)} options={multiOptions(choices.institutions)} allLabel="Todas" />
      <FilterMultiSelect label="Área" values={filters.area} onChange={(value) => onChange("area", value)} options={multiOptions(choices.areas)} allLabel="Todas" />
      <FilterMultiSelect label="Grande área" values={filters.largeArea} onChange={(value) => onChange("largeArea", value)} options={multiOptions(choices.largeAreas)} allLabel="Todas" />
      <FilterMultiSelect label="Território" values={filters.territory} onChange={(value) => onChange("territory", value)} options={multiOptions(choices.territories)} allLabel="Todos" />
    </section>
  );
}
