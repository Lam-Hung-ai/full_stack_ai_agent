import type { Workspace } from "../types/workspace.types";

export function pickWorkspace(
  workspaces: readonly Workspace[],
  selectedId: string | null,
): Workspace | undefined {
  return (
    workspaces.find((workspace) => workspace.id === selectedId) ??
    workspaces.find((workspace) => workspace.kind === "personal") ??
    workspaces[0]
  );
}

export function workspaceLabel(workspace: Workspace): string {
  return workspace.kind === "personal" ? "Cá nhân" : (workspace.name ?? "Tổ chức");
}
