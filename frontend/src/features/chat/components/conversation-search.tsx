"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { ArchiveIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useConversationSearch } from "../hooks/use-conversations";
import type { ConversationSearchItem } from "../types/chat.types";
import { highlight } from "../utils/search";

/** Chats matching `term`; each opens on the branch of its matching message. */
export function ConversationSearchResults({
  workspaceId,
  term,
}: {
  workspaceId: string;
  term: string;
}) {
  const results = useConversationSearch(workspaceId, term);

  if (results.isLoading) {
    return (
      <div className="flex flex-col gap-2 p-1">
        <Skeleton className="h-10" />
        <Skeleton className="h-10" />
      </div>
    );
  }
  if (results.isError) {
    return <p className="p-2 text-destructive text-sm">Không tìm được. Vui lòng thử lại.</p>;
  }
  const items = results.data?.pages.flatMap((page) => page.data) ?? [];
  if (items.length === 0) {
    return <p className="px-2 py-1 text-muted-foreground text-sm">Không có kết quả.</p>;
  }
  return (
    <>
      <ul aria-label="Kết quả tìm kiếm" className="flex flex-col gap-0.5">
        {items.map((item) => (
          <SearchResult item={item} key={item.id} term={term} />
        ))}
      </ul>
      {results.hasNextPage && (
        <Button
          className="w-full justify-start text-muted-foreground"
          disabled={results.isFetchingNextPage}
          onClick={() => void results.fetchNextPage()}
          size="sm"
          variant="ghost"
        >
          {results.isFetchingNextPage ? "Đang tải…" : "Xem thêm"}
        </Button>
      )}
    </>
  );
}

function SearchResult({ item, term }: { item: ConversationSearchItem; term: string }) {
  const pathname = usePathname();
  const message = useSearchParams().get("m");
  const href = item.message_id ? `/c/${item.id}?m=${item.message_id}` : `/c/${item.id}`;
  const active = pathname === `/c/${item.id}` && message === (item.message_id ?? null);
  return (
    <li>
      <Link
        aria-current={active ? "page" : undefined}
        className={cn(
          "flex flex-col gap-0.5 rounded-md px-2 py-1.5 text-sm hover:bg-accent",
          active && "bg-accent",
        )}
        href={href}
      >
        <span className="flex items-center gap-1.5 truncate font-medium">
          {item.archived_at && (
            <ArchiveIcon
              aria-label="Đã lưu trữ"
              className="size-3 shrink-0 text-muted-foreground"
            />
          )}
          <Highlighted term={term} text={item.title} />
        </span>
        {item.snippet && (
          <span className="line-clamp-2 text-muted-foreground text-xs">
            <Highlighted term={term} text={item.snippet} />
          </span>
        )}
      </Link>
    </li>
  );
}

function Highlighted({ text, term }: { text: string; term: string }) {
  return (
    <span className="truncate">
      {highlight(text, term).map((part, index) =>
        part.match ? (
          <mark
            className="rounded-sm bg-yellow-200/70 text-inherit dark:bg-yellow-500/30"
            key={index}
          >
            {part.text}
          </mark>
        ) : (
          <span key={index}>{part.text}</span>
        ),
      )}
    </span>
  );
}
