"use client";

import { BuildingIcon, CheckIcon, UserIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import {
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
} from "@/components/ui/dropdown-menu";
import { useCurrentWorkspace, useSelectWorkspace, useWorkspaces } from "../hooks/use-workspaces";
import type { Workspace } from "../types/workspace.types";
import { workspaceLabel } from "../utils/pick-workspace";

function WorkspaceIcon({ workspace }: { workspace: Workspace }) {
  return workspace.kind === "personal" ? <UserIcon /> : <BuildingIcon />;
}

/**
 * Submenu of the account menu: the current workspace, the others to switch
 * to, and `actions` composed in by the app (organization admin links).
 */
export function WorkspaceMenu({ actions }: { actions?: React.ReactNode }) {
  const router = useRouter();
  const { data } = useWorkspaces();
  const current = useCurrentWorkspace();
  const selectWorkspace = useSelectWorkspace();
  if (!data || !current) return null;

  const choose = (workspaceId: string) => {
    if (workspaceId === current.id) return;
    selectWorkspace(workspaceId);
    // An open chat belongs to the previous workspace.
    router.push("/");
  };

  return (
    <DropdownMenuSub>
      <DropdownMenuSubTrigger>
        <WorkspaceIcon workspace={current} />
        <span className="truncate">{workspaceLabel(current)}</span>
      </DropdownMenuSubTrigger>
      <DropdownMenuSubContent className="w-64">
        <DropdownMenuLabel className="text-muted-foreground text-xs">
          Không gian làm việc
        </DropdownMenuLabel>
        {data.data.map((workspace) => (
          <DropdownMenuItem key={workspace.id} onSelect={() => choose(workspace.id)}>
            <WorkspaceIcon workspace={workspace} />
            <span className="truncate">{workspaceLabel(workspace)}</span>
            {workspace.id === current.id && <CheckIcon className="ml-auto" />}
          </DropdownMenuItem>
        ))}
        {actions && (
          <>
            <DropdownMenuSeparator />
            {actions}
          </>
        )}
      </DropdownMenuSubContent>
    </DropdownMenuSub>
  );
}

/** Name of the current workspace, for the account button. */
export function CurrentWorkspaceName() {
  const current = useCurrentWorkspace();
  return current ? workspaceLabel(current) : null;
}
