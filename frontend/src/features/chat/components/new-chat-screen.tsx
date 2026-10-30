"use client";

import { useRouter } from "next/navigation";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useCurrentWorkspace } from "@/features/workspaces";
import { useCreateConversation } from "../hooks/use-conversations";
import { usePendingMessageStore } from "../stores/pending-message-store";
import { ChatComposer, type ComposerDraft } from "./chat-composer";
import { ChatEmptyState } from "./chat-empty-state";
import { ChatMessages } from "./chat-messages";

/** A chat that does not exist yet: the first question creates it. */
export function NewChatScreen() {
  const router = useRouter();
  const workspace = useCurrentWorkspace();
  const create = useCreateConversation(workspace?.id);
  const setPending = usePendingMessageStore((state) => state.setPending);

  const start = async (draft: ComposerDraft) => {
    if (create.isPending) return false;
    try {
      const conversation = await create.mutateAsync();
      setPending(conversation.id, draft);
      router.push(`/c/${conversation.id}`);
      return true;
    } catch {
      return false; // shown by create.isError; the draft stays
    }
  };

  return (
    <div className="mx-auto flex h-full w-full max-w-3xl flex-col p-4">
      <ChatMessages empty={<ChatEmptyState />} isBusy={false} rows={[]} />
      {create.isError && (
        <Alert variant="destructive">
          <AlertDescription>Không tạo được cuộc trò chuyện. Vui lòng thử lại.</AlertDescription>
        </Alert>
      )}
      <ChatComposer
        disabled={!workspace}
        onSubmit={start}
        workspaceId={workspace?.id}
        status={create.isPending ? "submitted" : "ready"}
      />
    </div>
  );
}
