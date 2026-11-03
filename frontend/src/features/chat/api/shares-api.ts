import { apiClient } from "@/lib/api";
import type { components } from "@/generated/api/schema";

export type Share = components["schemas"]["ShareResponse"];

export function getShare(conversationId: string, signal?: AbortSignal) {
  return apiClient<Share>(`/api/v1/conversations/${conversationId}/share`, { signal });
}

/** Publish the chat as it is now; the link stays the same. */
export function publishShare(conversationId: string) {
  return apiClient<Share>(`/api/v1/conversations/${conversationId}/share`, { method: "POST" });
}

export function revokeShare(conversationId: string) {
  return apiClient<void>(`/api/v1/conversations/${conversationId}/share`, { method: "DELETE" });
}
