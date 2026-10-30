import { apiClient } from "@/lib/api";
import type { components } from "@/generated/api/schema";

type Schemas = components["schemas"];
export type UploadCreate = Schemas["UploadCreate"];
export type UploadResponse = Schemas["UploadResponse"];
export type ChatFile = Schemas["FileResponse"];
export type FileLink = Schemas["DownloadResponse"];

export function createUpload(workspaceId: string, input: UploadCreate) {
  return apiClient<UploadResponse>(`/api/v1/workspaces/${workspaceId}/uploads`, {
    method: "POST",
    body: input,
  });
}

export function completeUpload(workspaceId: string, fileId: string, input: UploadCreate) {
  return apiClient<ChatFile>(`/api/v1/workspaces/${workspaceId}/uploads/${fileId}/complete`, {
    method: "POST",
    body: input,
  });
}

export function getFileLink(conversationId: string, fileId: string, signal?: AbortSignal) {
  return apiClient<FileLink>(`/api/v1/conversations/${conversationId}/files/${fileId}`, {
    signal,
  });
}
