"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MoreHorizontalIcon, PinIcon } from "lucide-react";
import {
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import type { ConversationListItem } from "../types/chat.types";
import { ConversationActionsMenu } from "./conversation-actions-menu";

/** One chat in the sidebar; its menu shows on hover. */
export function ConversationItem({
  conversation,
  workspaceId,
  icon,
}: {
  conversation: ConversationListItem;
  workspaceId: string;
  /** Shown before the title; by default a pin on a pinned chat. */
  icon?: React.ReactNode;
}) {
  const href = `/c/${conversation.id}`;
  const active = usePathname() === href;
  const { isMobile, setOpenMobile } = useSidebar();

  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild isActive={active} title={conversation.title}>
        <Link
          aria-current={active ? "page" : undefined}
          href={href}
          // On a phone the sidebar is a sheet over the chat being opened.
          onClick={() => isMobile && setOpenMobile(false)}
        >
          {icon ??
            (conversation.pinned_at && (
              <PinIcon aria-label="Đã ghim" className="text-muted-foreground" />
            ))}
          <span>{conversation.title}</span>
        </Link>
      </SidebarMenuButton>
      <ConversationActionsMenu conversation={conversation} workspaceId={workspaceId}>
        <SidebarMenuAction aria-label={`Thao tác cho ${conversation.title}`} showOnHover={!active}>
          <MoreHorizontalIcon />
        </SidebarMenuAction>
      </ConversationActionsMenu>
    </SidebarMenuItem>
  );
}
