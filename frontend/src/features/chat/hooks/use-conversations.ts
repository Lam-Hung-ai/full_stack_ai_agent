"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createConversation, listConversations } from "../api/conversations-api";

export const chatKeys = {
  // Workspace-scoped, so switching workspace drops them (WorkspaceSwitcher).
  conversations: (workspaceId: string) => ["workspaces", workspaceId, "conversations"] as const,
  history: (conversationId: string) => ["conversations", conversationId, "messages"] as const,
};

export function useConversations(workspaceId: string | undefined) {
  return useQuery({
    queryKey: chatKeys.conversations(workspaceId ?? ""),
    queryFn: ({ signal }) => listConversations(workspaceId!, signal),
    enabled: !!workspaceId,
  });
}

export function useCreateConversation(workspaceId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => createConversation(workspaceId!),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations(workspaceId!) }),
  });
}
