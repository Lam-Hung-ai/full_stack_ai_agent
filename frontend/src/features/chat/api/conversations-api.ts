import { apiClient } from "@/lib/api";
import type { Conversation, ConversationList, History } from "../types/chat.types";

export function listConversations(workspaceId: string, signal?: AbortSignal) {
  return apiClient<ConversationList>(`/api/v1/workspaces/${workspaceId}/conversations`, {
    query: { page: 1, page_size: 100 },
    signal,
  });
}

export function createConversation(workspaceId: string) {
  return apiClient<Conversation>(`/api/v1/workspaces/${workspaceId}/conversations`, {
    method: "POST",
    body: {},
  });
}

export function getHistory(conversationId: string, signal?: AbortSignal) {
  return apiClient<History>(`/api/v1/conversations/${conversationId}/messages`, { signal });
}
