"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PlusIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useCurrentWorkspace } from "@/features/workspaces";
import { cn } from "@/lib/utils";
import { useConversations } from "../hooks/use-conversations";

export function ConversationSidebar() {
  const pathname = usePathname();
  const workspace = useCurrentWorkspace();
  const conversations = useConversations(workspace?.id);

  return (
    <nav aria-label="Cuộc trò chuyện" className="flex h-full flex-col gap-2 p-2">
      <Button asChild className="justify-start" size="sm" variant="outline">
        <Link href="/">
          <PlusIcon />
          Chat mới
        </Link>
      </Button>
      <div className="min-h-0 flex-1 overflow-y-auto">
        {conversations.isLoading && (
          <div className="flex flex-col gap-2 p-1">
            <Skeleton className="h-7" />
            <Skeleton className="h-7" />
          </div>
        )}
        {conversations.isError && (
          <p className="p-2 text-destructive text-sm">Không tải được danh sách.</p>
        )}
        {conversations.data?.data.length === 0 && (
          <p className="p-2 text-muted-foreground text-sm">Chưa có cuộc trò chuyện nào.</p>
        )}
        <ul className="flex flex-col gap-0.5">
          {conversations.data?.data.map((conversation) => {
            const href = `/c/${conversation.id}`;
            const active = pathname === href;
            return (
              <li key={conversation.id}>
                <Link
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "block truncate rounded-md px-2 py-1.5 text-sm hover:bg-accent",
                    active && "bg-accent font-medium",
                  )}
                  href={href}
                  title={conversation.title}
                >
                  {conversation.title}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
