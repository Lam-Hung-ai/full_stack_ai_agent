"use client";

import { useState } from "react";
import { DownloadIcon } from "lucide-react";
import { toast } from "sonner";
import { DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { useCurrentWorkspace } from "@/features/workspaces";
import { saveBlob } from "@/lib/download";
import { exportConversations } from "../api/conversations-api";

/** Menu item: download the user's own chats of the current workspace (O08). */
export function ExportChatsMenuItem() {
  const workspace = useCurrentWorkspace();
  const [busy, setBusy] = useState(false);
  if (!workspace) return null;

  const download = async () => {
    setBusy(true);
    try {
      const { blob, name } = await exportConversations(workspace.id);
      saveBlob(blob, name);
    } catch {
      toast.error("Không export được. Vui lòng thử lại sau.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <DropdownMenuItem disabled={busy} onSelect={() => void download()}>
      <DownloadIcon />
      {busy ? "Đang export…" : "Export chat"}
    </DropdownMenuItem>
  );
}
