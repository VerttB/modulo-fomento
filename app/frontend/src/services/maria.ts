import type { MariaConversation, MariaConversationDetail, MariaMessage } from "../core/entities/maria";
import { API_BASE, requestJson } from "./http";

const BASE = `${API_BASE}/maria/conversations`;

export function listConversations(offset = 0, signal?: AbortSignal) {
  return requestJson<{ conversations: MariaConversation[]; total: number }>(`${BASE}?offset=${offset}&limit=30`, signal);
}

export function createConversation(signal?: AbortSignal) {
  return requestJson<MariaConversation>(BASE, signal, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title: null }),
  });
}

export function getConversation(id: string, signal?: AbortSignal) {
  return requestJson<MariaConversationDetail>(`${BASE}/${encodeURIComponent(id)}`, signal);
}

export function getMessages(id: string, signal?: AbortSignal) {
  return requestJson<{ messages: MariaMessage[] }>(`${BASE}/${encodeURIComponent(id)}/messages`, signal);
}

export function sendMessage(id: string, content: string) {
  return requestJson<{ user_message: MariaMessage; assistant_message: MariaMessage }>(
    `${BASE}/${encodeURIComponent(id)}/messages`, undefined,
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content }) },
  );
}
