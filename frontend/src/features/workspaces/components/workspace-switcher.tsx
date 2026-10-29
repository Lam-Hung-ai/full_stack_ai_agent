"use client";

import { BuildingIcon, CheckIcon, ChevronsUpDownIcon, UserIcon } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useWorkspaceStore } from "@/stores/workspace-store";
import { useCurrentWorkspace, useWorkspaces } from "../hooks/use-workspaces";
import { workspaceLabel } from "../utils/pick-workspace";

export function WorkspaceSwitcher() {
  const queryClient = useQueryClient();
  const { data } = useWorkspaces();
  const current = useCurrentWorkspace();
  const selectWorkspace = useWorkspaceStore((state) => state.selectWorkspace);
  if (!data || !current) return null;

  const choose = (workspaceId: string) => {
    if (workspaceId === current.id) return;
    selectWorkspace(workspaceId);
    // Drop data of the previous workspace so it is never shown under the new one.
    queryClient.removeQueries({
      predicate: (query) =>
        query.queryKey[0] === "workspaces" && query.queryKey.length > 1,
    });
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button className="max-w-56 justify-between" size="sm" variant="outline">
          <span className="truncate">{workspaceLabel(current)}</span>
          <ChevronsUpDownIcon className="opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64">
        <DropdownMenuLabel>Không gian làm việc</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {data.data.map((workspace) => (
          <DropdownMenuItem key={workspace.id} onSelect={() => choose(workspace.id)}>
            {workspace.kind === "personal" ? <UserIcon /> : <BuildingIcon />}
            <span className="truncate">{workspaceLabel(workspace)}</span>
            {workspace.id === current.id && <CheckIcon className="ml-auto" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
