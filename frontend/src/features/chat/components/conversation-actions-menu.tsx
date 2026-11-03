"use client";

import { useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  ArchiveIcon,
  ArchiveRestoreIcon,
  FolderIcon,
  PencilIcon,
  PinIcon,
  PinOffIcon,
  Share2Icon,
  Trash2Icon,
} from "lucide-react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { NameDialog } from "@/components/shared/name-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useCurrentWorkspace } from "@/features/workspaces";
import { useConversationActions, useFolders } from "../hooks/use-conversations";
import type { ConversationListItem, ConversationUpdate } from "../types/chat.types";
import { ShareDialog } from "./share-dialog";

/**
 * A chat's menu (pin, rename, share, file, archive, delete) opened from
 * `children`, the trigger: a sidebar row's button or the chat's title.
 */
export function ConversationActionsMenu({
  conversation,
  workspaceId,
  align = "start",
  children,
}: {
  conversation: ConversationListItem;
  workspaceId: string;
  align?: "start" | "end";
  children: React.ReactNode;
}) {
  // Personal chats share by public link, organization chats internally.
  const isPersonal = useCurrentWorkspace()?.kind === "personal";
  const router = useRouter();
  const active = usePathname() === `/c/${conversation.id}`;
  const folders = useFolders(workspaceId).data?.data ?? [];
  const { update, remove } = useConversationActions(workspaceId);
  const [dialog, setDialog] = useState<"rename" | "share" | "delete" | null>(null);
  const archived = conversation.archived_at !== null;

  // Menu actions close at once: a failure is reported by a toast.
  const change = (changes: ConversationUpdate, leave = false) =>
    update.mutate(
      { id: conversation.id, changes },
      {
        onSuccess: () => leave && active && router.push("/"),
        onError: () => toast.error("Không cập nhật được cuộc trò chuyện. Vui lòng thử lại."),
      },
    );

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>{children}</DropdownMenuTrigger>
        <DropdownMenuContent align={align} className="w-52">
          {!archived && (
            <DropdownMenuItem onSelect={() => change({ pinned: !conversation.pinned_at })}>
              {conversation.pinned_at ? <PinOffIcon /> : <PinIcon />}
              {conversation.pinned_at ? "Bỏ ghim" : "Ghim"}
            </DropdownMenuItem>
          )}
          <DropdownMenuItem
            onSelect={() => {
              update.reset();
              setDialog("rename");
            }}
          >
            <PencilIcon />
            Đổi tên
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={() => setDialog("share")}>
            <Share2Icon />
            Chia sẻ
          </DropdownMenuItem>
          {!archived && (
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>
                <FolderIcon />
                Chuyển vào folder
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent className="w-48">
                {folders.length === 0 && (
                  <DropdownMenuItem disabled>Chưa có folder</DropdownMenuItem>
                )}
                {folders.map((folder) => (
                  <DropdownMenuItem
                    disabled={folder.id === conversation.folder_id}
                    key={folder.id}
                    onSelect={() => change({ folder_id: folder.id })}
                  >
                    <FolderIcon />
                    <span className="truncate">{folder.name}</span>
                  </DropdownMenuItem>
                ))}
                {conversation.folder_id && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onSelect={() => change({ folder_id: null })}>
                      Bỏ khỏi folder
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuSubContent>
            </DropdownMenuSub>
          )}
          <DropdownMenuItem onSelect={() => change({ archived: !archived }, !archived)}>
            {archived ? <ArchiveRestoreIcon /> : <ArchiveIcon />}
            {archived ? "Bỏ lưu trữ" : "Lưu trữ"}
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onSelect={() => setDialog("delete")} variant="destructive">
            <Trash2Icon />
            Xoá
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      {dialog === "rename" && (
        <NameDialog
          defaultName={conversation.title}
          error={update.isError ? "Không đổi được tên. Vui lòng thử lại." : null}
          isPending={update.isPending}
          label="Tên cuộc trò chuyện"
          onClose={() => setDialog(null)}
          onSubmit={(title) =>
            update.mutate(
              { id: conversation.id, changes: { title } },
              { onSuccess: () => setDialog(null) },
            )
          }
          title="Đổi tên cuộc trò chuyện"
        />
      )}
      {dialog === "share" && (
        <ShareDialog
          conversationId={conversation.id}
          isPersonal={isPersonal}
          onClose={() => setDialog(null)}
        />
      )}
      {dialog === "delete" && (
        <ConfirmDialog
          description={`"${conversation.title}" sẽ bị xoá khỏi danh sách.`}
          onClose={() => setDialog(null)}
          onConfirm={() =>
            remove.mutate(conversation.id, {
              onSuccess: () => active && router.push("/"),
              onError: () => toast.error("Không xoá được cuộc trò chuyện. Vui lòng thử lại."),
            })
          }
          title="Xoá cuộc trò chuyện?"
        />
      )}
    </>
  );
}
