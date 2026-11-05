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
export type MariaBlock =
  | { type: "text"; text: string }
  | { type: "suggestions"; questions: string[] }
  | { type: "table"; title: string | null; columns: MariaColumn[]; rows: Record<string, unknown>[]; truncated: boolean }
  | { type: "chart"; title: string; x: MariaColumn; group: MariaColumn | null; series: MariaColumn[]; data: Record<string, unknown>[]; truncated: boolean };

export interface MariaMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: MariaBlock[];
  created_at: string;
}
