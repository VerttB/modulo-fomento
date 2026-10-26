import { useMemo, useState } from "react";

export default function FilterMultiSelect({
  label,
  values = [],
  options,
  onChange,
  allLabel = "Todos",
}) {
  const [search, setSearch] = useState("");
  const visibleOptions = useMemo(() => {
    const normalizedSearch = search.trim().toLocaleLowerCase("pt-BR");
    if (!normalizedSearch) return options;
    return options.filter((option) =>
      option.label.toLocaleLowerCase("pt-BR").includes(normalizedSearch),
    );
  }, [options, search]);

  function toggle(value) {
    onChange(
      values.includes(value)
        ? values.filter((item) => item !== value)
        : [...values, value],
    );
  }

  return (
    <div className="filter-select filter-multiselect">
      <span>{label}</span>
      <details>
        <summary aria-label={`${label}: ${values.length ? `${values.length} selecionado(s)` : allLabel}`}>
          {values.length ? `${values.length} selecionado(s)` : allLabel}
          <span className="filter-multi-chevron" aria-hidden="true">⌄</span>
        </summary>
        <div className="filter-multi-menu">
          <input
            type="search"
            placeholder={`Buscar ${label.toLocaleLowerCase("pt-BR")}…`}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            aria-label={`Buscar opções de ${label.toLocaleLowerCase("pt-BR")}`}
          />
          {values.length > 0 && (
            <button className="filter-multi-clear" type="button" onClick={() => onChange([])}>
              Limpar seleção
            </button>
          )}
          <div className="filter-multi-options">
            {visibleOptions.map((option) => (
              <label key={option.value}>
                <input
                  type="checkbox"
                  checked={values.includes(option.value)}
                  onChange={() => toggle(option.value)}
                />
                <span>{option.label}</span>
              </label>
            ))}
            {visibleOptions.length === 0 && <small>Nenhuma opção encontrada.</small>}
          </div>
        </div>
      </details>
    </div>
  );
}
