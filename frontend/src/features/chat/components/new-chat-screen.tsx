"use client";

import { useRouter } from "next/navigation";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useCurrentWorkspace } from "@/features/workspaces";
import { useCreateConversation } from "../hooks/use-conversations";
import { usePendingMessageStore } from "../stores/pending-message-store";
import { ChatComposer } from "./chat-composer";
import { ChatEmptyState } from "./chat-empty-state";
import { ChatMessages } from "./chat-messages";

/** A chat that does not exist yet: the first question creates it. */
export function NewChatScreen() {
  const router = useRouter();
  const workspace = useCurrentWorkspace();
  const create = useCreateConversation(workspace?.id);
  const setPending = usePendingMessageStore((state) => state.setPending);

  const start = (text: string) => {
    if (!text.trim() || create.isPending) return;
    create.mutate(undefined, {
      onSuccess: (conversation) => {
        setPending(conversation.id, text);
        router.push(`/c/${conversation.id}`);
      },
    });
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
        status={create.isPending ? "submitted" : "ready"}
      />
    </div>
  );
}
