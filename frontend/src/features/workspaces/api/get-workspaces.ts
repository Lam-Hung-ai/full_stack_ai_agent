import { allPages, apiClient, MAX_PAGE_SIZE } from "@/lib/api";
import type { WorkspaceList } from "../types/workspace.types";

/** Personal workspace plus every organization with an active membership. */
export function getWorkspaces(signal?: AbortSignal) {
  return allPages((page) =>
    apiClient<WorkspaceList>("/api/v1/workspaces", {
      query: { page, page_size: MAX_PAGE_SIZE },
      signal,
    }),
  );
}
