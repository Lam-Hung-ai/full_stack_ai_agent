"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createConversation,
  getConversation,
  deleteConversation,
  listConversations,
  updateConversation,
} from "../api/conversations-api";
import { createFolder, deleteFolder, listFolders, renameFolder } from "../api/folders-api";
import type { ConversationFilter, ConversationUpdate } from "../types/chat.types";

export const chatKeys = {
  // Workspace-scoped, so switching workspace drops them (WorkspaceSwitcher).
  conversations: (workspaceId: string) => ["workspaces", workspaceId, "conversations"] as const,
  conversationList: (workspaceId: string, filter: ConversationFilter) =>
    [...chatKeys.conversations(workspaceId), filter] as const,
  folders: (workspaceId: string) => ["workspaces", workspaceId, "folders"] as const,
  conversation: (conversationId: string) => ["conversations", conversationId, "detail"] as const,
  histories: (conversationId: string) => ["conversations", conversationId, "messages"] as const,
  /** `fromMessageId` null is the saved branch. */
  history: (conversationId: string, fromMessageId: string | null) =>
    [...chatKeys.histories(conversationId), fromMessageId] as const,
};

/** One chat's metadata (its workspace, for attaching files). */
export function useConversation(conversationId: string) {
  return useQuery({
    queryKey: chatKeys.conversation(conversationId),
    queryFn: ({ signal }) => getConversation(conversationId, signal),
  });
}

export function useConversations(workspaceId: string | undefined, filter: ConversationFilter) {
  return useQuery({
    queryKey: chatKeys.conversationList(workspaceId ?? "", filter),
    queryFn: ({ signal }) => listConversations(workspaceId!, filter, signal),
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

/** Rename, pin, archive, file or delete chats of one workspace. */
export function useConversationActions(workspaceId: string) {
  const queryClient = useQueryClient();
  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: chatKeys.conversations(workspaceId) });
  const update = useMutation({
    mutationFn: ({ id, changes }: { id: string; changes: ConversationUpdate }) =>
      updateConversation(id, changes),
    onSuccess: refresh,
  });
  const remove = useMutation({
    mutationFn: (id: string) => deleteConversation(id),
    onSuccess: refresh,
  });
  return { update, remove };
}

export function useFolders(workspaceId: string | undefined) {
  return useQuery({
    queryKey: chatKeys.folders(workspaceId ?? ""),
    queryFn: ({ signal }) => listFolders(workspaceId!, signal),
    enabled: !!workspaceId,
  });
}

export function useFolderActions(workspaceId: string) {
  const queryClient = useQueryClient();
  const refreshFolders = () =>
    queryClient.invalidateQueries({ queryKey: chatKeys.folders(workspaceId) });
  const create = useMutation({
    mutationFn: (name: string) => createFolder(workspaceId, name),
    onSuccess: refreshFolders,
  });
  const rename = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => renameFolder(id, name),
    onSuccess: refreshFolders,
  });
  const remove = useMutation({
    mutationFn: (id: string) => deleteFolder(id),
    // Its chats move back to the main list.
    onSuccess: () =>
      Promise.all([
        refreshFolders(),
        queryClient.invalidateQueries({ queryKey: chatKeys.conversations(workspaceId) }),
      ]),
  });
  return { create, rename, remove };
}
