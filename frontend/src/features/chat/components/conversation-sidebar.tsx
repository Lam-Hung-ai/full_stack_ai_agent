"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ChevronDownIcon,
  FolderPlusIcon,
  MessageCircleIcon,
  PlusIcon,
  SearchIcon,
} from "lucide-react";
import { NameDialog } from "@/components/shared/name-dialog";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Kbd } from "@/components/ui/kbd";
import {
  SidebarGroup,
  SidebarGroupAction,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { useCurrentWorkspace } from "@/features/workspaces";
import { cn } from "@/lib/utils";
import { useConversations, useFolderActions, useFolders } from "../hooks/use-conversations";
import { useSidebarStore } from "../stores/sidebar-store";
import { folderErrorMessage } from "../utils/folders";
import { ConversationList } from "./conversation-list";
import { ConversationSearchDialog } from "./conversation-search";
import { FolderGroup } from "./folder-group";
import { RecentFilterMenu } from "./recent-filter-menu";

export function ConversationSidebar() {
  const workspace = useCurrentWorkspace();
  if (!workspace) return null;
  // Keyed: switching workspace resets the open sections and dialogs.
  return <WorkspaceSidebar key={workspace.id} workspaceId={workspace.id} />;
}

function WorkspaceSidebar({ workspaceId }: { workspaceId: string }) {
  const { isMobile, setOpenMobile } = useSidebar();
  const [searching, setSearching] = useState(false);

  // Ctrl+K (Cmd+K on a Mac) opens the search from anywhere.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() === "k" && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        setSearching(true);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <nav aria-label="Cuộc trò chuyện" className="flex flex-col">
      <SidebarGroup>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild tooltip="Chat mới">
              <Link href="/" onClick={() => isMobile && setOpenMobile(false)}>
                <PlusIcon />
                <span>Chat mới</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton onClick={() => setSearching(true)} tooltip="Tìm kiếm">
              <SearchIcon />
              <span className="flex-1">Tìm kiếm</span>
              <Kbd className="group-data-[collapsible=icon]:hidden">Ctrl K</Kbd>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarGroup>
      {/* The lists need the full width: the icon rail shows only the actions. */}
      <div className="flex flex-col group-data-[collapsible=icon]:hidden">
        <PinnedSection workspaceId={workspaceId} />
        <RecentSection workspaceId={workspaceId} />
      </div>
      {searching && (
        <ConversationSearchDialog onClose={() => setSearching(false)} workspaceId={workspaceId} />
      )}
    </nav>
  );
}

/** A sidebar section whose title folds it; content mounts only while open. */
function Section({
  title,
  defaultOpen = true,
  action,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <Collapsible asChild onOpenChange={setOpen} open={open}>
      <SidebarGroup className="py-1">
        <SidebarGroupLabel asChild className="w-fit gap-1 hover:text-sidebar-foreground">
          <CollapsibleTrigger>
            {title}
            <ChevronDownIcon
              className={cn("size-3! transition-transform", !open && "-rotate-90")}
            />
          </CollapsibleTrigger>
        </SidebarGroupLabel>
        {action}
        <CollapsibleContent asChild>
          <SidebarGroupContent>{open && children}</SidebarGroupContent>
        </CollapsibleContent>
      </SidebarGroup>
    </Collapsible>
  );
}

/** Folders and the pinned chats outside them, like Claude's "Pinned". */
function PinnedSection({ workspaceId }: { workspaceId: string }) {
  const folders = useFolders(workspaceId);
  const pinned = useConversations(workspaceId, { kind: "pinned" });
  const { create } = useFolderActions(workspaceId);
  const [creating, setCreating] = useState(false);
  const folderList = folders.data?.data ?? [];
  const isEmpty =
    folders.isSuccess &&
    folderList.length === 0 &&
    pinned.isSuccess &&
    pinned.data.pages[0]?.data.length === 0;

  return (
    <>
      <Section
        action={
          <SidebarGroupAction
            aria-label="Folder mới"
            className="top-2.5"
            onClick={() => setCreating(true)}
            title="Folder mới"
          >
            <FolderPlusIcon />
          </SidebarGroupAction>
        }
        title="Ghim"
      >
        {isEmpty ? (
          <p className="px-2 py-1 text-muted-foreground text-sm">
            Tạo folder hoặc ghim chat để giữ ở đây.
          </p>
        ) : (
          <>
            <SidebarMenu>
              {folderList.map((folder) => (
                <FolderGroup folder={folder} key={folder.id} workspaceId={workspaceId} />
              ))}
            </SidebarMenu>
            <ConversationList
              filter={{ kind: "pinned" }}
              itemIcon={<MessageCircleIcon className="text-muted-foreground" />}
              workspaceId={workspaceId}
            />
          </>
        )}
      </Section>
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
    </>
  );
}

/** Chats outside folders and not pinned, as the filter menu says. */
function RecentSection({ workspaceId }: { workspaceId: string }) {
  const { status, grouping, sort } = useSidebarStore();
  return (
    <Section action={<RecentFilterMenu />} title={status === "archived" ? "Đã lưu trữ" : "Gần đây"}>
      <ConversationList
        emptyText={
          status === "archived"
            ? "Không có cuộc trò chuyện lưu trữ."
            : "Chưa có cuộc trò chuyện nào."
        }
        filter={status === "archived" ? { kind: "archived", sort } : { kind: "recent", sort }}
        grouping={grouping}
        workspaceId={workspaceId}
      />
    </Section>
  );
}
