import { apiClient } from "@/lib/api";
import type {
  Conversation,
  ConversationFilter,
  ConversationList,
  ConversationUpdate,
  History,
  StopResult,
} from "../types/chat.types";

function filterQuery(filter: ConversationFilter) {
  switch (filter.kind) {
    case "unfiled":
      return { unfiled: true };
    case "folder":
      return { folder_id: filter.folderId };
    case "archived":
      return { archived: true };
  }
}

export function listConversations(
  workspaceId: string,
  filter: ConversationFilter,
  signal?: AbortSignal,
) {
  return apiClient<ConversationList>(`/api/v1/workspaces/${workspaceId}/conversations`, {
    query: { page: 1, page_size: 100, ...filterQuery(filter) },
    signal,
  });
}

export function createConversation(workspaceId: string) {
  return apiClient<Conversation>(`/api/v1/workspaces/${workspaceId}/conversations`, {
    method: "POST",
    body: {},
  });
}

export function updateConversation(conversationId: string, changes: ConversationUpdate) {
  return apiClient<Conversation>(`/api/v1/conversations/${conversationId}`, {
    method: "PATCH",
    body: changes,
  });
}

export function deleteConversation(conversationId: string) {
  return apiClient<void>(`/api/v1/conversations/${conversationId}`, { method: "DELETE" });
}

/** The saved branch, or with `fromMessageId` the branch through that message. */
export function getHistory(
  conversationId: string,
  { fromMessageId, signal }: { fromMessageId?: string | null; signal?: AbortSignal } = {},
) {
  return apiClient<History>(`/api/v1/conversations/${conversationId}/messages`, {
    query: { from_message_id: fromMessageId },
    signal,
  });
}

export function stopAssistant(conversationId: string, assistantMessageId: string) {
  return apiClient<StopResult>(
    `/api/v1/conversations/${conversationId}/messages/${assistantMessageId}/stop`,
    { method: "POST" },
  );
}
