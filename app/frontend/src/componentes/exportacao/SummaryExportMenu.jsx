import { useState } from "react";

const options = [
  ["cidade", "Cidade"],
  ["territorio", "Território de identidade"],
  ["instituicao", "Instituição"],
];
const allDimensions = options.map(([dimension]) => dimension);

export default function SummaryExportMenu({ disabled, loading, format, onExport }) {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(allDimensions);
  const allSelected = selected.length === allDimensions.length;

  function toggleAll() {
    setSelected(allSelected ? [] : allDimensions);
  }

  function toggleDimension(dimension) {
    setSelected((current) => current.includes(dimension)
      ? current.filter((item) => item !== dimension)
      : allDimensions.filter((item) => current.includes(item) || item === dimension));
  }

  async function exportSelected() {
    const completed = await onExport(selected);
    if (completed) setOpen(false);
  }

  return <div className="summary-export">
    <button
      className="export-button export-summary-button"
      type="button"
      disabled={disabled || loading}
      aria-expanded={open}
      aria-busy={loading}
      onClick={() => setOpen((current) => !current)}
    >
      {loading ? <><span className="export-spinner" aria-hidden="true" />Preparando…</> : <><span>▦</span> Exportar resumo <span className="summary-export-chevron">⌄</span></>}
    </button>
    {open && <div className="summary-export-menu" role="group" aria-label="Recortes para exportar">
      <strong>Escolha os recortes</strong>
      <label><input type="checkbox" checked={allSelected} onChange={toggleAll} /> Todos os recortes</label>
      <div className="summary-export-options">
        {options.map(([dimension, label]) => <label key={dimension}>
          <input
            type="checkbox"
            checked={selected.includes(dimension)}
            onChange={() => toggleDimension(dimension)}
          />
          {label}
        </label>)}
      </div>
      <button type="button" disabled={!selected.length || loading} aria-busy={loading} onClick={exportSelected}>
        {loading && <span className="export-spinner" aria-hidden="true" />}
        {loading ? "Preparando arquivo…" : `Baixar ${format.toUpperCase()}`}
      </button>
    </div>}
  </div>;
}
