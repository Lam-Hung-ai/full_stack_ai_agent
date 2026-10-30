"use client";

import type { ChatStatus } from "ai";
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  PromptInputSubmit,
  PromptInputTextarea,
} from "@/components/ai-elements/prompt-input";

export function ChatComposer({
  status,
  disabled,
  onSubmit,
}: {
  status: ChatStatus;
  disabled?: boolean;
  onSubmit: (text: string) => void;
}) {
  return (
    <PromptInput className="mt-4" onSubmit={(message) => onSubmit(message.text)}>
      <PromptInputBody>
        <PromptInputTextarea placeholder="Nhập câu hỏi…" />
      </PromptInputBody>
      <PromptInputFooter>
        <span className="text-muted-foreground text-xs">Enter để gửi, Shift+Enter để xuống dòng</span>
        <PromptInputSubmit disabled={disabled} status={status} />
      </PromptInputFooter>
    </PromptInput>
  );
}
