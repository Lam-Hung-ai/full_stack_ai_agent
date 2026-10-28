"use client";

import { BrainIcon, ChevronDownIcon } from "lucide-react";
import { useReasoning } from "@/components/ai-elements/reasoning";
import { latestLine } from "@/lib/agui-messages";
import { cn } from "@/lib/utils";

/**
 * Contents of a `ReasoningTrigger`: the live summary line while the model is
 * thinking, a settled label once it has stopped.
 */
export function ReasoningSummary({
  reasoning,
  isStreaming,
}: {
  reasoning: string;
  isStreaming: boolean;
}) {
  const { isOpen } = useReasoning();

  return (
    <>
      <BrainIcon className="size-4 shrink-0" />
      {isStreaming ? (
        <span className="min-w-0 flex-1 truncate text-left">{latestLine(reasoning)}</span>
      ) : (
        <span>Thought for a few seconds</span>
      )}
      <ChevronDownIcon
        className={cn("size-4 shrink-0 transition-transform", isOpen ? "rotate-180" : "rotate-0")}
      />
    </>
  );
}
