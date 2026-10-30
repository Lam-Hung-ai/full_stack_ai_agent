"use client";

import { BuildingIcon, CheckIcon, ChevronsUpDownIcon, UserIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useCurrentWorkspace, useSelectWorkspace, useWorkspaces } from "../hooks/use-workspaces";
import { workspaceLabel } from "../utils/pick-workspace";

/** `actions`: menu items composed in by the app (organization admin links). */
export function WorkspaceSwitcher({ actions }: { actions?: React.ReactNode }) {
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
        {actions && (
          <>
            <DropdownMenuSeparator />
            {actions}
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
