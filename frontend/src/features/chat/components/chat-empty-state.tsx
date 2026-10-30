import { SparklesIcon } from "lucide-react";
import { ConversationEmptyState } from "@/components/ai-elements/conversation";

export function ChatEmptyState() {
  return (
    <ConversationEmptyState
      description="Hỏi bất cứ điều gì — agent trả lời và có thể dùng công cụ."
      icon={<SparklesIcon className="size-6" />}
      title="Bắt đầu cuộc trò chuyện"
    />
  );
}
