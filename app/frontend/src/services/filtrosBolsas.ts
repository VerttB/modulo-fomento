import type { ScholarshipFilters } from "../core/types/filters";

const filterFields: Record<keyof ScholarshipFilters, string> = {
  from: "ano_inicio", to: "ano_fim", modality: "modalidade", city: "cidade",
  institution: "instituicao", area: "area", largeArea: "grande_area",
  territory: "territorio_identidade",
};

export function filterParams(filters: ScholarshipFilters): URLSearchParams {
  const params = new URLSearchParams();
  for (const [key, apiField] of Object.entries(filterFields) as Array<[keyof ScholarshipFilters, string]>) {
    const value = filters[key];
    if (Array.isArray(value)) {
      value.filter((item) => item.trim()).forEach((item) => params.append(apiField, item));
    } else if (value.trim()) {
      params.set(apiField, value);
    }
  }
  return params;
}
