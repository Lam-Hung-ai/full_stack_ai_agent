import type { Message as AGUIMessage, ToolCall } from "@ag-ui/client";
import {
  type ActivityMessage,
  buildItems,
  findToolResult,
  type ToolResultMessage,
} from "./agui-messages";
import { ASK_USER_TOOL } from "./interactions";

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
