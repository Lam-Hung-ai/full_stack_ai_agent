"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Command as CommandPrimitive } from "cmdk";
import { ArchiveIcon, MessageCircleIcon, SearchIcon, XIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandDialog,
  CommandGroup,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { DialogClose } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { cn } from "@/lib/utils";
import { useConversationSearch, useConversations } from "../hooks/use-conversations";
import type { ConversationSearchItem } from "../types/chat.types";
import { highlight, searchTerm } from "../utils/search";

const SEARCH_DELAY_MS = 300;

/**
 * Search over the workspace's chats by name and content. Before a term is
 * typed it lists the recent chats; a result opens on its matching turn.
 */
export function ConversationSearchDialog({
  workspaceId,
  onClose,
}: {
  workspaceId: string;
  onClose: () => void;
}) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const term = searchTerm(useDebouncedValue(query, SEARCH_DELAY_MS));
  const open = (href: string) => {
    onClose();
    router.push(href);
  };

  return (
    <CommandDialog
      className="top-[12%] sm:max-w-2xl"
      description="Tìm theo tên hoặc nội dung cuộc trò chuyện"
      onOpenChange={(isOpen) => !isOpen && onClose()}
      open
      title="Tìm kiếm"
    >
      {/* Results come from the server, already filtered and ranked. */}
      <Command className="p-0" shouldFilter={false}>
        <div className="flex items-center gap-3 border-b px-5 py-3">
          <SearchIcon className="size-4 shrink-0 text-muted-foreground" />
          <CommandPrimitive.Input
            className="h-9 flex-1 bg-transparent text-base outline-none placeholder:text-muted-foreground"
            onValueChange={setQuery}
            placeholder="Tìm kiếm cuộc trò chuyện…"
            value={query}
          />
          <DialogClose asChild>
            <Button aria-label="Đóng" size="icon-sm" variant="ghost">
              <XIcon />
            </Button>
          </DialogClose>
        </div>
        <CommandList className="max-h-[min(28rem,60dvh)] p-2">
          {term ? (
            <SearchResults onOpen={open} term={term} workspaceId={workspaceId} />
          ) : (
            <RecentChats onOpen={open} workspaceId={workspaceId} />
          )}
        </CommandList>
      </Command>
    </CommandDialog>
  );
}

const ITEM_CLASS = "gap-3 px-3 py-2.5";

function RecentChats({
  workspaceId,
  onOpen,
}: {
  workspaceId: string;
  onOpen: (href: string) => void;
}) {
  const recent = useConversations(workspaceId, { kind: "unfiled" });
  const items = recent.data?.pages[0]?.data ?? [];
  if (recent.isLoading) return <Loading />;
  if (items.length === 0) return <Note>Chưa có cuộc trò chuyện nào.</Note>;
  return (
    <CommandGroup heading="Cuộc trò chuyện gần đây">
      {items.map((item) => (
        <CommandItem
          className={ITEM_CLASS}
          key={item.id}
          onSelect={() => onOpen(`/c/${item.id}`)}
          value={item.id}
        >
          <MessageCircleIcon className="text-muted-foreground" />
          <span className="truncate">{item.title}</span>
        </CommandItem>
      ))}
    </CommandGroup>
  );
}

function SearchResults({
  workspaceId,
  term,
  onOpen,
}: {
  workspaceId: string;
  term: string;
  onOpen: (href: string) => void;
}) {
  const results = useConversationSearch(workspaceId, term);
  if (results.isLoading) return <Loading />;
  if (results.isError) {
    return <Note className="text-destructive">Không tìm được. Vui lòng thử lại.</Note>;
  }
  const items = results.data?.pages.flatMap((page) => page.data) ?? [];
  if (items.length === 0) return <Note>Không có kết quả.</Note>;
  return (
    <CommandGroup heading="Kết quả">
      {items.map((item) => (
        <SearchResult item={item} key={item.id} onOpen={onOpen} term={term} />
      ))}
      {results.hasNextPage && (
        <CommandItem
          className={cn(ITEM_CLASS, "justify-center text-muted-foreground")}
          disabled={results.isFetchingNextPage}
          onSelect={() => void results.fetchNextPage()}
          value="more"
        >
          {results.isFetchingNextPage ? "Đang tải…" : "Xem thêm kết quả"}
        </CommandItem>
      )}
    </CommandGroup>
  );
}

function SearchResult({
  item,
  term,
  onOpen,
}: {
  item: ConversationSearchItem;
  term: string;
  onOpen: (href: string) => void;
}) {
  const href = item.turn_id ? `/c/${item.id}?t=${item.turn_id}` : `/c/${item.id}`;
  const Icon = item.archived_at ? ArchiveIcon : MessageCircleIcon;
  return (
    <CommandItem
      className={cn(ITEM_CLASS, "items-start")}
      onSelect={() => onOpen(href)}
      value={`${item.id}:${item.turn_id ?? ""}`}
    >
      <Icon
        aria-label={item.archived_at ? "Đã lưu trữ" : undefined}
        className="mt-0.5 text-muted-foreground"
      />
      <span className="flex min-w-0 flex-1 flex-col gap-0.5">
        <span className="truncate font-medium">
          <Highlighted term={term} text={item.title} />
        </span>
        {item.snippet && (
          <span className="line-clamp-2 text-muted-foreground text-xs">
            <Highlighted term={term} text={item.snippet} />
          </span>
        )}
      </span>
    </CommandItem>
  );
}

function Highlighted({ text, term }: { text: string; term: string }) {
  return highlight(text, term).map((part, index) =>
    part.match ? (
      <mark className="rounded-sm bg-yellow-200/70 text-inherit dark:bg-yellow-500/30" key={index}>
        {part.text}
      </mark>
    ) : (
      <span key={index}>{part.text}</span>
    ),
  );
}

function Loading() {
  return (
    <div aria-busy className="flex flex-col gap-2 p-2">
      <Skeleton className="h-9" />
      <Skeleton className="h-9" />
      <Skeleton className="h-9" />
    </div>
  );
}

function Note({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <p className={cn("px-3 py-6 text-center text-muted-foreground text-sm", className)}>
      {children}
    </p>
  );
}
