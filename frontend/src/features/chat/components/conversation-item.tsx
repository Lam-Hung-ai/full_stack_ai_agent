"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  ArchiveIcon,
  ArchiveRestoreIcon,
  FolderIcon,
  MoreHorizontalIcon,
  PencilIcon,
  PinIcon,
  PinOffIcon,
  Share2Icon,
  Trash2Icon,
} from "lucide-react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { NameDialog } from "@/components/shared/name-dialog";
import { Button } from "@/components/ui/button";
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
import { cn } from "@/lib/utils";
import { useConversationActions } from "../hooks/use-conversations";
import type { ConversationListItem, ConversationUpdate, Folder } from "../types/chat.types";
import { ShareDialog } from "./share-dialog";

/** One chat in the sidebar with its menu: pin, rename, share, file, archive, delete. */
export function ConversationItem({
  conversation,
  workspaceId,
  folders,
}: {
  conversation: ConversationListItem;
  workspaceId: string;
  folders: readonly Folder[];
}) {
  // Personal chats share by public link, organization chats internally.
  const isPersonal = useCurrentWorkspace()?.kind === "personal";
  const router = useRouter();
  const pathname = usePathname();
  const href = `/c/${conversation.id}`;
  const active = pathname === href;
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
    <li className="group/item relative">
      <Link
        aria-current={active ? "page" : undefined}
        className={cn(
          "flex items-center gap-1.5 truncate rounded-md py-1.5 pr-8 pl-2 text-sm hover:bg-accent",
          active && "bg-accent font-medium",
        )}
        href={href}
        title={conversation.title}
      >
        {conversation.pinned_at && (
          <PinIcon aria-label="Đã ghim" className="size-3 shrink-0 text-muted-foreground" />
        )}
        <span className="truncate">{conversation.title}</span>
      </Link>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            aria-label={`Thao tác cho ${conversation.title}`}
            className={cn(
              "absolute top-1/2 right-1 -translate-y-1/2 opacity-0 group-hover/item:opacity-100 focus-visible:opacity-100 data-[state=open]:opacity-100",
              active && "opacity-100",
            )}
            size="icon-xs"
            variant="ghost"
          >
            <MoreHorizontalIcon />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-52">
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
    </li>
  );
}
