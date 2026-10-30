"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArchiveIcon,
  ChevronRightIcon,
  FolderPlusIcon,
  PlusIcon,
  SearchIcon,
  XIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { useCurrentWorkspace } from "@/features/workspaces";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { cn } from "@/lib/utils";
import { useFolderActions, useFolders } from "../hooks/use-conversations";
import { ConversationList } from "./conversation-list";
import { ConversationSearchResults } from "./conversation-search";
import { searchTerm } from "../utils/search";
import { folderErrorMessage } from "../utils/folders";
import { FolderGroup } from "./folder-group";
import { NameDialog } from "@/components/shared/name-dialog";

const SEARCH_DELAY_MS = 300;

export function ConversationSidebar() {
  const workspace = useCurrentWorkspace();
  if (!workspace) return null;
  // Keyed: switching workspace resets the open sections and dialogs.
  return <WorkspaceSidebar key={workspace.id} workspaceId={workspace.id} />;
}

function WorkspaceSidebar({ workspaceId }: { workspaceId: string }) {
  const folders = useFolders(workspaceId);
  const { create } = useFolderActions(workspaceId);
  const [creating, setCreating] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [query, setQuery] = useState("");
  const term = searchTerm(useDebouncedValue(query, SEARCH_DELAY_MS));
  const folderList = folders.data?.data ?? [];

  return (
    <nav aria-label="Cuộc trò chuyện" className="flex h-full flex-col gap-2 p-2">
      <Button asChild className="justify-start" size="sm" variant="outline">
        <Link href="/">
          <PlusIcon />
          Chat mới
        </Link>
      </Button>
      <div className="relative">
        <SearchIcon className="-translate-y-1/2 pointer-events-none absolute top-1/2 left-2 size-3.5 text-muted-foreground" />
        <Input
          aria-label="Tìm cuộc trò chuyện"
          className="h-8 pr-7 pl-7 text-sm"
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => event.key === "Escape" && setQuery("")}
          placeholder="Tìm theo tên hoặc nội dung"
          value={query}
        />
        {query && (
          <Button
            aria-label="Xoá tìm kiếm"
            className="-translate-y-1/2 absolute top-1/2 right-1"
            onClick={() => setQuery("")}
            size="icon-xs"
            variant="ghost"
          >
            <XIcon />
          </Button>
        )}
      </div>
      {term ? (
        <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
          <ConversationSearchResults term={term} workspaceId={workspaceId} />
        </div>
      ) : (
        <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto">
          <section aria-labelledby="sidebar-folders">
            <div className="flex items-center justify-between px-2">
              <h2 className="font-medium text-muted-foreground text-xs" id="sidebar-folders">
                Folder
              </h2>
              <Button
                aria-label="Folder mới"
                onClick={() => setCreating(true)}
                size="icon-xs"
                variant="ghost"
              >
                <FolderPlusIcon />
              </Button>
            </div>
            {folderList.map((folder) => (
              <FolderGroup
                folder={folder}
                folders={folderList}
                key={folder.id}
                workspaceId={workspaceId}
              />
            ))}
          </section>
          <section aria-labelledby="sidebar-chats">
            <h2 className="px-2 pb-1 font-medium text-muted-foreground text-xs" id="sidebar-chats">
              Cuộc trò chuyện
            </h2>
            <ConversationList
              emptyText="Chưa có cuộc trò chuyện nào."
              filter={{ kind: "unfiled" }}
              folders={folderList}
              workspaceId={workspaceId}
            />
          </section>
        </div>
      )}
      <Collapsible onOpenChange={setShowArchived} open={showArchived}>
        <CollapsibleTrigger className="flex w-full items-center gap-1.5 rounded-md px-2 py-1.5 text-muted-foreground text-sm hover:bg-accent">
          <ChevronRightIcon
            className={cn("size-3.5 transition-transform", showArchived && "rotate-90")}
          />
          <ArchiveIcon className="size-3.5" />
          Đã lưu trữ
        </CollapsibleTrigger>
        <CollapsibleContent className="max-h-60 overflow-y-auto">
          {showArchived && (
            <ConversationList
              emptyText="Không có cuộc trò chuyện lưu trữ."
              filter={{ kind: "archived" }}
              folders={folderList}
              workspaceId={workspaceId}
            />
          )}
        </CollapsibleContent>
      </Collapsible>
      {creating && (
        <NameDialog
          error={create.isError ? folderErrorMessage(create.error) : null}
          isPending={create.isPending}
          label="Tên folder"
          onClose={() => {
            create.reset();
            setCreating(false);
          }}
          onSubmit={(name) => create.mutate(name, { onSuccess: () => setCreating(false) })}
          submitLabel="Tạo"
          title="Folder mới"
        />
      )}
    </nav>
  );
}
