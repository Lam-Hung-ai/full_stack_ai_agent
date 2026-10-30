import { apiClient } from "@/lib/api";
import type { components } from "@/generated/api/schema";

type Schemas = components["schemas"];
export type SharedConversation = Schemas["SharedConversation"];
export type SharedMessage = Schemas["SharedMessage"];
export type CopyResult = Schemas["CopyResponse"];
type FileLink = Schemas["DownloadResponse"];

const base = (token: string) => `/api/v1/shares/${encodeURIComponent(token)}`;

export function getSharedConversation(token: string, signal?: AbortSignal) {
  return apiClient<SharedConversation>(base(token), { signal });
}

export function getSharedFileLink(token: string, fileId: string, signal?: AbortSignal) {
  return apiClient<FileLink>(`${base(token)}/files/${fileId}`, { signal });
}

/** Same `clientRequestId` again returns the same copy (a retry). */
export function copySharedConversation(token: string, clientRequestId: string) {
  return apiClient<CopyResult>(`${base(token)}/copy`, {
    method: "POST",
    body: { client_request_id: clientRequestId },
  });
}
