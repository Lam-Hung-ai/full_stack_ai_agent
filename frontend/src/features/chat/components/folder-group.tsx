"use client";

import { useState } from "react";
import {
  FolderIcon,
  FolderOpenIcon,
  MoreHorizontalIcon,
  PencilIcon,
  Trash2Icon,
} from "lucide-react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { NameDialog } from "@/components/shared/name-dialog";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SidebarMenuAction, SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar";
import { useFolderActions } from "../hooks/use-conversations";
import type { Folder } from "../types/chat.types";
import { folderErrorMessage } from "../utils/folders";
import { ConversationList } from "./conversation-list";

/** A folder that lists its chats, indented under a guide line, when opened. */
export function FolderGroup({ folder, workspaceId }: { folder: Folder; workspaceId: string }) {
  const [open, setOpen] = useState(false);
  const [dialog, setDialog] = useState<"rename" | "delete" | null>(null);
  const { rename, remove } = useFolderActions(workspaceId);

  return (
    <Collapsible asChild onOpenChange={setOpen} open={open}>
      <SidebarMenuItem>
        <CollapsibleTrigger asChild>
          <SidebarMenuButton title={folder.name}>
            {open ? <FolderOpenIcon /> : <FolderIcon />}
            <span>{folder.name}</span>
          </SidebarMenuButton>
        </CollapsibleTrigger>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuAction aria-label={`Thao tác cho folder ${folder.name}`} showOnHover>
              <MoreHorizontalIcon />
            </SidebarMenuAction>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            <DropdownMenuItem onSelect={() => setDialog("rename")}>
              <PencilIcon />
              Đổi tên
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={() => setDialog("delete")} variant="destructive">
              <Trash2Icon />
              Xoá folder
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <CollapsibleContent className="ml-3.5 border-sidebar-border border-l pl-1.5">
          {open && (
            <ConversationList
              emptyText="Folder trống."
              filter={{ kind: "folder", folderId: folder.id }}
              workspaceId={workspaceId}
            />
          )}
        </CollapsibleContent>
        {dialog === "rename" && (
          <NameDialog
            defaultName={folder.name}
            error={rename.isError ? folderErrorMessage(rename.error) : null}
            isPending={rename.isPending}
            label="Tên folder"
            onClose={() => {
              rename.reset();
              setDialog(null);
            }}
            onSubmit={(name) =>
              rename.mutate({ id: folder.id, name }, { onSuccess: () => setDialog(null) })
            }
            title="Đổi tên folder"
          />
        )}
        {dialog === "delete" && (
          <ConfirmDialog
            description="Các cuộc trò chuyện trong folder được giữ lại và chuyển về danh sách chung."
            onClose={() => setDialog(null)}
            onConfirm={() =>
              remove.mutate(folder.id, {
                onError: () => toast.error("Không xoá được folder. Vui lòng thử lại."),
              })
            }
            title={`Xoá folder "${folder.name}"?`}
          />
        )}
      </SidebarMenuItem>
    </Collapsible>
  );
}
