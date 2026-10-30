"use client";

import { useEffect } from "react";
import { Loader } from "@/components/ai-elements/loader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { useConversationChat } from "../hooks/use-conversation-chat";
import { usePendingMessageStore } from "../stores/pending-message-store";
import { chatErrorMessage } from "../utils/history";
import { ChatComposer } from "./chat-composer";
import { ChatEmptyState } from "./chat-empty-state";
import { ChatMessages } from "./chat-messages";

export function ConversationScreen({ conversationId }: { conversationId: string }) {
  const chat = useConversationChat(conversationId);
  const take = usePendingMessageStore((state) => state.take);
  const { isReady, sendMessage } = chat;

  // The question typed on the new-chat screen, sent once the chat is ready.
  useEffect(() => {
    if (!isReady) return;
    const text = take(conversationId);
    if (text) void sendMessage(text);
  }, [conversationId, isReady, sendMessage, take]);

  if (chat.isLoading) {
    return (
      <div className="flex h-full items-center justify-center" aria-busy="true">
        <Spinner aria-label="Đang tải cuộc trò chuyện" />
      </div>
    );
  }
  if (chat.loadError) {
    return (
      <div className="mx-auto w-full max-w-3xl p-4">
        <Alert variant="destructive">
          <AlertDescription>Không tìm thấy cuộc trò chuyện hoặc bạn không có quyền xem.</AlertDescription>
        </Alert>
      </div>
    );
  }

  const isBusy = chat.status === "submitted" || chat.status === "streaming";
  return (
    <div className="mx-auto flex h-full w-full max-w-3xl flex-col p-4">
      <ChatMessages empty={<ChatEmptyState />} isBusy={isBusy} messages={chat.messages} />
      {(chat.status === "submitted" || chat.remoteTurnRunning) && (
        <div className="flex items-center gap-2 py-2 text-muted-foreground text-sm">
          <Loader />
          {chat.remoteTurnRunning ? "Câu trả lời đang được tạo…" : null}
        </div>
      )}
      {chat.error && (
        <Alert variant="destructive">
          <AlertDescription>{chatErrorMessage(chat.error)}</AlertDescription>
        </Alert>
      )}
      <ChatComposer
        disabled={chat.remoteTurnRunning}
        onSubmit={(text) => void sendMessage(text)}
        status={chat.status}
      />
    </div>
  );
}
