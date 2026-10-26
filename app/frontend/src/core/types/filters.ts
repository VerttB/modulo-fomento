export interface ScholarshipFilters {
  from: string;
  to: string;
  modality: string[];
  city: string[];
  institution: string[];
  area: string[];
  largeArea: string[];
  territory: string[];
}

export type ScholarshipFilterKey = keyof ScholarshipFilters;

export const emptyScholarshipFilters: ScholarshipFilters = {
  from: "",
  to: "",
  modality: [],
  city: [],
  institution: [],
  area: [],
  largeArea: [],
  territory: [],
};
