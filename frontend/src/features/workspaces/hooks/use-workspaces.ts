"use client";

import { useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useWorkspaceStore } from "@/stores/workspace-store";
import { getWorkspaces } from "../api/get-workspaces";
import type { Workspace } from "../types/workspace.types";
import { pickWorkspace } from "../utils/pick-workspace";

export const workspaceKeys = {
  all: ["workspaces"] as const,
};

export function useWorkspaces() {
  return useQuery({
    queryKey: workspaceKeys.all,
    queryFn: ({ signal }) => getWorkspaces(signal),
  });
}

/** The workspace the UI works in: the stored choice while still accessible,
 *  otherwise the personal workspace. */
export function useCurrentWorkspace(): Workspace | undefined {
  const { data } = useWorkspaces();
  const selectedId = useWorkspaceStore((state) => state.selectedWorkspaceId);
  return data ? pickWorkspace(data.data, selectedId) : undefined;
}

/** Switch the UI to another workspace, dropping data cached for the
 *  previous one so it is never shown under the new one. */
export function useSelectWorkspace() {
  const queryClient = useQueryClient();
  const selectWorkspace = useWorkspaceStore((state) => state.selectWorkspace);
  return useCallback(
    (workspaceId: string) => {
      selectWorkspace(workspaceId);
      queryClient.removeQueries({
        predicate: (query) => query.queryKey[0] === "workspaces" && query.queryKey.length > 1,
      });
    },
    [queryClient, selectWorkspace],
  );
}
