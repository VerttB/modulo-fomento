export interface MariaConversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  total_tokens: number;
}

export interface MariaConversationDetail extends MariaConversation {
  questions_asked: number;
  questions_limit: number | null;
}

export interface MariaColumn { key: string; label: string }

export interface MariaBlockOrigin {
  sources: string[];
  description: string;
  queried_at: string;
  coverage: { keys: number; found: number } | null;
}

export interface MariaResearcherMetrics {
  articles: number;
  book_chapters: number;
  books: number;
  patents: number;
  software: number;
  brand: number;
  total_productions: number;
  h_index: number | null;
  i10_index: number | null;
  citations: number | null;
}

export interface MariaResearcherAffiliation {
  institution_id: string | null;
  institution_name: string | null;
  institution_acronym: string | null;
  city_name: string | null;
}

export interface MariaEvidenceItem {
  type: string;
  title: string | null;
  year: number | null;
}

export interface MariaResearcherEvidence {
  total: number;
  by_type: Record<string, number>;
  items: MariaEvidenceItem[];
}

export interface MariaResearcherCard {
  id: string;
  name: string;
  lattes_id: string | null;
  abstract: string | null;
  photo_url: string | null;
  city: string | null;
  state: string | null;
  territory: string | null;
  graduation: string | null;
  openalex_id: string | null;
  orcid: string | null;
  affiliations: MariaResearcherAffiliation[];
  metrics: MariaResearcherMetrics;
  evidence: MariaResearcherEvidence | null;
}

export interface MariaRankingInfo {
  term: string;
  criterion: string;
  fields: string[];
  data_as_of: string | null;
}

export interface MariaProductionAuthor {
  name: string;
  lattes_id: string | null;
  order: number | null;
}

export interface MariaProductionDetails {
  qualis: string | null;
  doi: string | null;
  issn: string | null;
  isbn: string | null;
  magazine: string | null;
  event_name: string | null;
  event_city: string | null;
  nature: string | null;
  grant_date: string | null;
  status: string | null;
}

export interface MariaProductionCard {
  id: string;
  title: string;
  type: "article" | "book" | "book_chapter" | "patent" | "software" | "event";
  type_label: string;
  year: number | null;
  authors: MariaProductionAuthor[];
  details: MariaProductionDetails;
}

export type MariaBlock =
  | { type: "text"; text: string }
  | { type: "suggestions"; questions: string[] }
  | { type: "table"; title: string | null; columns: MariaColumn[]; rows: Record<string, unknown>[]; truncated: boolean }
  | { type: "chart"; title: string; x: MariaColumn; group: MariaColumn | null; series: MariaColumn[]; data: Record<string, unknown>[]; truncated: boolean }
  | {
      type: "researchers";
      title: string | null;
      researchers: MariaResearcherCard[];
      total: number;
      truncated: boolean;
      origin: MariaBlockOrigin | null;
      ranking: MariaRankingInfo | null;
    }
  | {
      type: "productions";
      title: string | null;
      productions: MariaProductionCard[];
      total: number;
      truncated: boolean;
      origin: MariaBlockOrigin | null;
    };

export interface MariaMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: MariaBlock[];
  created_at: string;
}
