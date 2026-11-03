import { apiClient } from "@/lib/api";
import type { Folder, FolderList } from "../types/chat.types";

export function listFolders(workspaceId: string, signal?: AbortSignal) {
  return apiClient<FolderList>(`/api/v1/workspaces/${workspaceId}/folders`, {
    query: { page: 1, page_size: 100 },
    signal,
  });
}

export function createFolder(workspaceId: string, name: string) {
  return apiClient<Folder>(`/api/v1/workspaces/${workspaceId}/folders`, {
    method: "POST",
    body: { name },
  });
}

export function renameFolder(folderId: string, name: string) {
  return apiClient<Folder>(`/api/v1/folders/${folderId}`, { method: "PATCH", body: { name } });
}

export function deleteFolder(folderId: string) {
  return apiClient<void>(`/api/v1/folders/${folderId}`, { method: "DELETE" });
}
