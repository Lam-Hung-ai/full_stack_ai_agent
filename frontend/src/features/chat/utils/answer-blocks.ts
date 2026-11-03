import type { Message as AGUIMessage, ToolCall } from "@ag-ui/client";
import type { RowView } from "../types/chat.types";
import {
  type ActivityMessage,
  buildItems,
  findToolResult,
  type ToolResultMessage,
} from "./agui-messages";
import { ASK_USER_TOOL } from "./interactions";
import { formatDuration } from "./turn-time";

/** One step of the agent's work, shown in the trace above the answer. */
export type WorkStep =
  | { kind: "thinking"; id: string; text: string }
  /** Text the model wrote between steps ("Let me check…"). */
  | { kind: "note"; id: string; text: string }
  | { kind: "tool"; id: string; call: ToolCall; result?: ToolResultMessage };

/**
 * What an assistant row renders, in order: runs of work steps, the agent's
 * questions to the user, and the answer text.
 */
export type AnswerBlock =
  | { kind: "work"; id: string; steps: WorkStep[] }
  | { kind: "activity"; message: ActivityMessage }
  | { kind: "text"; id: string; text: string };

type Entry =
  | WorkStep
  | { kind: "activity"; message: ActivityMessage }
  | { kind: "text"; id: string; text: string };

/**
 * Splits a row's AG-UI bundle like Kimi: thinking, tool calls and the text
 * written between them are work; only text after the last step is the
 * answer. ask_user calls show as their question cards, not as tools.
 */
export function answerBlocks(messages: readonly AGUIMessage[]): AnswerBlock[] {
  const entries: Entry[] = [];
  for (const item of buildItems(messages)) {
    if (item.kind === "activity") {
      entries.push(item);
      continue;
    }
    const { message, reasoning } = item.turn;
    if (message.role !== "assistant") continue;
    if (reasoning)
      entries.push({ kind: "thinking", id: `${message.id}:reasoning`, text: reasoning });
    if (message.content?.trim()) {
      entries.push({ kind: "text", id: message.id, text: message.content });
    }
    for (const call of message.toolCalls ?? []) {
      if (call.function.name === ASK_USER_TOOL) continue;
      entries.push({ kind: "tool", id: call.id, call, result: findToolResult(messages, call.id) });
    }
  }

  const lastStep = entries.findLastIndex(
    (entry) => entry.kind === "thinking" || entry.kind === "tool",
  );
  const blocks: AnswerBlock[] = [];
  entries.forEach((entry, index) => {
    if (entry.kind === "activity") {
      blocks.push(entry);
      return;
    }
    if (entry.kind === "text" && index > lastStep) {
      blocks.push(entry);
      return;
    }
    const step: WorkStep = entry.kind === "text" ? { ...entry, kind: "note" } : entry;
    const last = blocks.at(-1);
    if (last?.kind === "work") last.steps.push(step);
    else blocks.push({ kind: "work", id: step.id, steps: [step] });
  });
  return blocks;
}

/** The answer's own words, for copying: its text blocks without the work. */
export function answerCopyText(blocks: readonly AnswerBlock[]): string {
  return blocks.flatMap((block) => (block.kind === "text" ? [block.text.trim()] : [])).join("\n\n");
}

/**
 * The header of a run of work. While it runs it counts the seconds; once
 * the row ends, the last run tells how it ended (stopped, failed) and the
 * first run of a completed row how long the whole answer took.
 */
export function workSummary({
  running,
  elapsed,
  status,
  workTime,
  isFirst,
  isLast,
}: {
  running: boolean;
  /** Seconds this tab has watched it run; 0 before the first tick. */
  elapsed: number;
  status: RowView["status"];
  /** The finished row's duration, as formatted text. */
  workTime: string | null;
  isFirst: boolean;
  isLast: boolean;
}): string {
  if (running) return elapsed > 0 ? `Đang làm việc… ${formatDuration(elapsed)}` : "Đang làm việc…";
  if (isLast && status === "cancelled") return workTime ? `Đã dừng sau ${workTime}` : "Đã dừng";
  if (isLast && status === "failed") return workTime ? `Gặp lỗi sau ${workTime}` : "Gặp lỗi";
  if (isFirst && status === "completed" && workTime) return `Đã làm việc trong ${workTime}`;
  return "Đã làm việc";
}
