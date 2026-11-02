"use client";

import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSkeleton,
} from "@/components/ui/sidebar";
import { useConversations } from "../hooks/use-conversations";
import type { ConversationFilter } from "../types/chat.types";
import { ConversationItem } from "./conversation-item";

/** The chats matching one sidebar filter; pinned ones come first (backend). */
export function ConversationList({
  workspaceId,
  filter,
  emptyText,
}: {
  workspaceId: string;
  filter: ConversationFilter;
  emptyText: string;
}) {
  const conversations = useConversations(workspaceId, filter);

  if (conversations.isLoading) {
    return (
      <SidebarMenu>
        <SidebarMenuSkeleton />
        <SidebarMenuSkeleton />
      </SidebarMenu>
    );
  }
  if (conversations.isError) {
    return <p className="px-2 py-1 text-destructive text-sm">Không tải được danh sách.</p>;
  }
  const items = conversations.data?.pages.flatMap((page) => page.data) ?? [];
  if (items.length === 0) {
    return <p className="px-2 py-1 text-muted-foreground text-sm">{emptyText}</p>;
  }
  return (
    <SidebarMenu>
      {items.map((conversation) => (
        <ConversationItem
          conversation={conversation}
          key={conversation.id}
          workspaceId={workspaceId}
        />
      ))}
      {conversations.hasNextPage && (
        <SidebarMenuItem>
          <SidebarMenuButton
            className="text-muted-foreground"
            disabled={conversations.isFetchingNextPage}
            onClick={() => void conversations.fetchNextPage()}
          >
            <span>{conversations.isFetchingNextPage ? "Đang tải…" : "Xem thêm"}</span>
          </SidebarMenuButton>
        </SidebarMenuItem>
      )}
    </SidebarMenu>
  );
}
