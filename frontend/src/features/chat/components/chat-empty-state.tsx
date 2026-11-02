import { SparklesIcon } from "lucide-react";
import { ConversationEmptyState } from "@/components/ai-elements/conversation";

export function ChatEmptyState() {
  return (
    <ConversationEmptyState className="size-auto">
      <div className="flex items-center gap-3">
        <SparklesIcon className="size-7 text-primary" />
        <h2 className="font-semibold text-2xl tracking-tight">Hôm nay bạn cần gì?</h2>
      </div>
      <p className="text-muted-foreground text-sm">
        Hỏi bất cứ điều gì — agent trả lời và có thể dùng công cụ.
      </p>
    </ConversationEmptyState>
  );
}
