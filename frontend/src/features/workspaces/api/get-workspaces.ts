import { apiClient } from "@/lib/api";
import type { WorkspaceList } from "../types/workspace.types";

/** Personal workspace plus every organization with an active membership. */
export function getWorkspaces(signal?: AbortSignal) {
  return apiClient<WorkspaceList>("/api/v1/workspaces", {
    query: { page: 1, page_size: 100 },
    signal,
  });
}
