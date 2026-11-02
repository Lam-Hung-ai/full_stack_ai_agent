"use client";

import { SidebarMenu, SidebarMenuSkeleton } from "@/components/ui/sidebar";
import { useOnVisible } from "@/hooks/use-on-visible";
import { useConversations } from "../hooks/use-conversations";
import type { RecentGrouping } from "../stores/sidebar-store";
import type { ConversationFilter, ConversationListItem } from "../types/chat.types";
import { groupByDay } from "../utils/sidebar";
import { ConversationItem } from "./conversation-item";

/**
 * The chats matching one sidebar filter, pinned first (backend). A page
 * loads at a time; the next one when the list is scrolled to its end.
 */
export function ConversationList({
  workspaceId,
  filter,
  grouping = "none",
  itemIcon,
  emptyText,
}: {
  workspaceId: string;
  filter: ConversationFilter;
  grouping?: RecentGrouping;
  /** Shown before each title (see ConversationItem). */
  itemIcon?: React.ReactNode;
  /** Without it an empty list shows nothing. */
  emptyText?: string;
}) {
  const conversations = useConversations(workspaceId, filter);
  const { hasNextPage, isFetchingNextPage, fetchNextPage } = conversations;
  const more = useOnVisible<HTMLDivElement>(
    () => void fetchNextPage(),
    hasNextPage && !isFetchingNextPage,
  );

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
    return emptyText ? (
      <p className="px-2 py-1 text-muted-foreground text-sm">{emptyText}</p>
    ) : null;
  }

  const menu = (chats: readonly ConversationListItem[]) => (
    <SidebarMenu>
      {chats.map((conversation) => (
        <ConversationItem
          conversation={conversation}
          icon={itemIcon}
          key={conversation.id}
          workspaceId={workspaceId}
        />
      ))}
    </SidebarMenu>
  );
  const sortedByCreation = "sort" in filter && filter.sort === "created";

  return (
    <>
      {grouping === "day"
        ? groupByDay(items, (chat) => (sortedByCreation ? chat.created_at : chat.updated_at)).map(
            (group, index) => (
              // A label can repeat when a pinned chat leads the list.
              <section aria-label={group.label} key={`${index}-${group.label}`}>
                <h3 className="px-2 pt-2 pb-1 text-muted-foreground text-xs">{group.label}</h3>
                {menu(group.items)}
              </section>
            ),
          )
        : menu(items)}
      {hasNextPage && (
        <div aria-busy={isFetchingNextPage} ref={more}>
          <SidebarMenuSkeleton />
        </div>
      )}
    </>
  );
}
