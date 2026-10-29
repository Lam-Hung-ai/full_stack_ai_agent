import type { Message as AGUIMessage } from "@ag-ui/client";

/**
 * Shaping an AG-UI message array into something renderable.
 *
 * Pure and framework-free on purpose: this is the one place that knows how the
 * AG-UI event stream's quirks map onto turns, so a second client (or a test)
 * can reuse it without pulling in React or a transport.
 */

export type TurnMessage = Extract<AGUIMessage, { role: "user" | "assistant" }>;
export type Turn = { message: TurnMessage; reasoning?: string };
export type ToolResultMessage = Extract<AGUIMessage, { role: "tool" }>;

/** Marks the placeholder turn that carries reasoning arriving before its assistant message. */
export const PENDING_REASONING_ID = "__pending-reasoning__";

/**
 * AG-UI streams a standalone `reasoning` message before the `assistant` message
 * it belongs to, with no shared id, so each one is paired with the assistant
 * turn that follows it.
 */
export function buildTurns(messages: readonly AGUIMessage[]): Turn[] {
  const turns: Turn[] = [];
  let pendingReasoning: string | undefined;

  for (const message of messages) {
    if (message.role === "reasoning") {
      pendingReasoning = message.content;
      continue;
    }
    if (message.role === "user" || message.role === "assistant") {
      turns.push({
        message,
        reasoning: message.role === "assistant" ? pendingReasoning : undefined,
      });
      pendingReasoning = undefined;
    }
  }

  // The assistant message doesn't exist yet while reasoning is still streaming
  // (TEXT_MESSAGE_START only fires after REASONING_END), so without this the
  // entire reasoning phase renders nothing — reasoning only became visible once
  // the run finished. A placeholder turn makes it show up immediately.
  if (pendingReasoning !== undefined) {
    turns.push({
      message: { id: PENDING_REASONING_ID, role: "assistant", content: "" },
      reasoning: pendingReasoning,
    });
  }

  return turns;
}

export function findToolResult(
  messages: readonly AGUIMessage[],
  toolCallId: string,
): ToolResultMessage | undefined {
  return messages.find((m) => m.role === "tool" && m.toolCallId === toolCallId) as
    | ToolResultMessage
    | undefined;
}

/**
 * Best-effort parse of a tool call's streamed `arguments` string.
 *
 * Falls back to the raw string while the JSON is still incomplete, so a card
 * rendered mid-stream shows the partial text rather than throwing.
 */
export function parseToolArgs(raw: string): unknown {
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

/**
 * The latest non-blank line of a reasoning stream, for the collapsed summary.
 * A stalled model visibly stalls and a fast one visibly moves, without having
 * to expand the panel to tell the difference.
 */
export function latestLine(text: string): string {
  const visible = text.trimEnd();
  const newline = visible.lastIndexOf("\n");
  return newline === -1 ? visible : visible.slice(newline + 1);
}
