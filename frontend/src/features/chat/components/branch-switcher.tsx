"use client";

import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react";
import { MessageAction } from "@/components/ai-elements/message";

/** "‹ 2/3 ›" between the versions of one message; hidden with one version. */
export function BranchSwitcher({
  currentId,
  siblingIds,
  disabled,
  onSwitch,
}: {
  currentId: string;
  siblingIds: readonly string[];
  disabled?: boolean;
  onSwitch: (messageId: string) => void;
}) {
  const index = siblingIds.indexOf(currentId);
  if (siblingIds.length < 2 || index === -1) return null;
  return (
    <div className="flex items-center text-muted-foreground text-xs">
      <MessageAction
        disabled={disabled || index === 0}
        label="Phiên bản trước"
        onClick={() => onSwitch(siblingIds[index - 1])}
      >
        <ChevronLeftIcon />
      </MessageAction>
      <span aria-live="polite" className="tabular-nums">
        {index + 1}/{siblingIds.length}
      </span>
      <MessageAction
        disabled={disabled || index === siblingIds.length - 1}
        label="Phiên bản sau"
        onClick={() => onSwitch(siblingIds[index + 1])}
      >
        <ChevronRightIcon />
      </MessageAction>
    </div>
  );
}
