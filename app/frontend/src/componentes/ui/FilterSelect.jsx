import { ChevronDown } from "lucide-react";

export default function FilterSelect({ label, value, options, onChange }) {
  return (
    <label className={`filter-select ${value ? "is-active" : ""}`}>
      <span>{label}</span>
      <div className="filter-control">
        <select value={value} onChange={(event) => onChange(event.target.value)}>
          {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
        <ChevronDown className="filter-control-chevron" size={14} aria-hidden="true" />
      </div>
    </label>
  );
}
