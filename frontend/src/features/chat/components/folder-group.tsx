"use client";

import { useState } from "react";
import {
  ChevronRightIcon,
  FolderIcon,
  MoreHorizontalIcon,
  PencilIcon,
  Trash2Icon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { useFolderActions } from "../hooks/use-conversations";
import type { Folder } from "../types/chat.types";
import { folderErrorMessage } from "../utils/folders";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { ConversationList } from "./conversation-list";
import { NameDialog } from "@/components/shared/name-dialog";

/** A folder that lists its chats when opened. */
export function FolderGroup({
  folder,
  folders,
  workspaceId,
}: {
  folder: Folder;
  folders: readonly Folder[];
  workspaceId: string;
}) {
  const [open, setOpen] = useState(false);
  const [dialog, setDialog] = useState<"rename" | "delete" | null>(null);
  const { rename, remove } = useFolderActions(workspaceId);

  return (
    <Collapsible onOpenChange={setOpen} open={open}>
      <div className="group/folder relative">
        <CollapsibleTrigger className="flex w-full items-center gap-1.5 rounded-md py-1.5 pr-8 pl-2 text-left text-sm hover:bg-accent">
          <ChevronRightIcon
            className={cn("size-3.5 shrink-0 transition-transform", open && "rotate-90")}
          />
          <FolderIcon className="size-3.5 shrink-0 text-muted-foreground" />
          <span className="truncate">{folder.name}</span>
        </CollapsibleTrigger>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              aria-label={`Thao tác cho folder ${folder.name}`}
              className="absolute top-1/2 right-1 -translate-y-1/2 opacity-0 group-hover/folder:opacity-100 focus-visible:opacity-100 data-[state=open]:opacity-100"
              size="icon-xs"
              variant="ghost"
            >
              <MoreHorizontalIcon />
            </Button>
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
      </div>
      <CollapsibleContent className="pl-4">
        {open && (
          <ConversationList
            emptyText="Folder trống."
            filter={{ kind: "folder", folderId: folder.id }}
            folders={folders}
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
          onConfirm={() => remove.mutate(folder.id)}
          title={`Xoá folder "${folder.name}"?`}
        />
      )}
    </Collapsible>
  );
}
