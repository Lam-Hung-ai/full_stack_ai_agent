"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronDownIcon, FolderPlusIcon, PlusIcon, SearchIcon } from "lucide-react";
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
import { useFolderActions, useFolders } from "../hooks/use-conversations";
import { folderErrorMessage } from "../utils/folders";
import { ConversationList } from "./conversation-list";
import { ConversationSearchDialog } from "./conversation-search";
import { FolderGroup } from "./folder-group";

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
        <FoldersSection workspaceId={workspaceId} />
        <Section title="Gần đây">
          <ConversationList
            emptyText="Chưa có cuộc trò chuyện nào."
            filter={{ kind: "unfiled" }}
            workspaceId={workspaceId}
          />
        </Section>
        <Section defaultOpen={false} title="Đã lưu trữ">
          <ConversationList
            emptyText="Không có cuộc trò chuyện lưu trữ."
            filter={{ kind: "archived" }}
            workspaceId={workspaceId}
          />
        </Section>
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

function FoldersSection({ workspaceId }: { workspaceId: string }) {
  const folders = useFolders(workspaceId);
  const { create } = useFolderActions(workspaceId);
  const [creating, setCreating] = useState(false);
  const folderList = folders.data?.data ?? [];

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
        title="Folder"
      >
        {folders.isSuccess && folderList.length === 0 ? (
          <p className="px-2 py-1 text-muted-foreground text-sm">Chưa có folder.</p>
        ) : (
          <SidebarMenu>
            {folderList.map((folder) => (
              <FolderGroup folder={folder} key={folder.id} workspaceId={workspaceId} />
            ))}
          </SidebarMenu>
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
