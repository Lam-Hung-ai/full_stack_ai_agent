"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/lib/api";
import { getShare, publishShare, revokeShare } from "../api/shares-api";
import { chatKeys } from "./use-conversations";

const shareKey = (conversationId: string) => [...chatKeys.conversation(conversationId), "share"];

/** The chat's share; `null` when it has none (404 is an answer here). */
export function useShare(conversationId: string) {
  return useQuery({
    queryKey: shareKey(conversationId),
    queryFn: async ({ signal }) => {
      try {
        return await getShare(conversationId, signal);
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
      }
    },
  });
}

export function useShareActions(conversationId: string) {
  const queryClient = useQueryClient();
  return {
    publish: useMutation({
      mutationFn: () => publishShare(conversationId),
      onSuccess: (share) => queryClient.setQueryData(shareKey(conversationId), share),
    }),
    revoke: useMutation({
      mutationFn: () => revokeShare(conversationId),
      onSuccess: () => queryClient.setQueryData(shareKey(conversationId), null),
    }),
  };
}
