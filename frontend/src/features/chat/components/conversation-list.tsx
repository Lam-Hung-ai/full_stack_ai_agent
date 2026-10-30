"use client";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useConversations } from "../hooks/use-conversations";
import type { ConversationFilter, Folder } from "../types/chat.types";
import { ConversationItem } from "./conversation-item";

/** The chats matching one sidebar filter; pinned ones come first (backend). */
export function ConversationList({
  workspaceId,
  filter,
  folders,
  emptyText,
}: {
  workspaceId: string;
  filter: ConversationFilter;
  folders: readonly Folder[];
  emptyText: string;
}) {
  const conversations = useConversations(workspaceId, filter);

  if (conversations.isLoading) {
    return (
      <div className="flex flex-col gap-2 p-1">
        <Skeleton className="h-7" />
        <Skeleton className="h-7" />
      </div>
    );
  }
  if (conversations.isError) {
    return <p className="p-2 text-destructive text-sm">Không tải được danh sách.</p>;
  }
  const items = conversations.data?.pages.flatMap((page) => page.data) ?? [];
  if (items.length === 0) {
    return <p className="px-2 py-1 text-muted-foreground text-sm">{emptyText}</p>;
  }
  return (
    <>
      <ul className="flex flex-col gap-0.5">
        {items.map((conversation) => (
          <ConversationItem
            conversation={conversation}
            folders={folders}
            key={conversation.id}
            workspaceId={workspaceId}
          />
        ))}
      </ul>
      {conversations.hasNextPage && (
        <Button
          className="w-full justify-start text-muted-foreground"
          disabled={conversations.isFetchingNextPage}
          onClick={() => void conversations.fetchNextPage()}
          size="sm"
          variant="ghost"
        >
          {conversations.isFetchingNextPage ? "Đang tải…" : "Xem thêm"}
        </Button>
      )}
    </>
  );
}
