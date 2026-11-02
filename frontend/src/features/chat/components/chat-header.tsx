"use client";

import { useState } from "react";
import { ChevronDownIcon, Share2Icon } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { useCurrentWorkspace } from "@/features/workspaces";
import type { Conversation } from "../types/chat.types";
import { ConversationActionsMenu } from "./conversation-actions-menu";
import { ShareDialog } from "./share-dialog";

/** Top bar of an open chat: its title opens the chat's menu; share on the right. */
export function ChatHeader({ conversation }: { conversation?: Conversation }) {
  const isPersonal = useCurrentWorkspace()?.kind === "personal";
  const [sharing, setSharing] = useState(false);

  return (
    <PageHeader
      className="border-b"
      end={
        conversation && (
          <Button onClick={() => setSharing(true)} size="sm" variant="ghost">
            <Share2Icon />
            Chia sẻ
          </Button>
        )
      }
    >
      {conversation && (
        <ConversationActionsMenu
          conversation={conversation}
          workspaceId={conversation.workspace_id}
        >
          <Button className="min-w-0 max-w-full font-normal" size="sm" variant="ghost">
            <span className="truncate">{conversation.title}</span>
            <ChevronDownIcon className="text-muted-foreground" />
          </Button>
        </ConversationActionsMenu>
      )}
      {sharing && conversation && (
        <ShareDialog
          conversationId={conversation.id}
          isPersonal={isPersonal}
          onClose={() => setSharing(false)}
        />
      )}
    </PageHeader>
  );
}
