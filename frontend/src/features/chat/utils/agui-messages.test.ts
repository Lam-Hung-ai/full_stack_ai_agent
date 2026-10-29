import { describe, expect, it } from "vitest";
import type { Message as AGUIMessage } from "@ag-ui/client";
import {
  PENDING_REASONING_ID,
  buildTurns,
  findToolResult,
  latestLine,
  parseToolArgs,
} from "./agui-messages";

describe("buildTurns", () => {
  it("pairs reasoning with the assistant message that follows it", () => {
    const messages: AGUIMessage[] = [
      { id: "u1", role: "user", content: "Hi" },
      { id: "r1", role: "reasoning", content: "thinking" },
      { id: "a1", role: "assistant", content: "Hello" },
    ];
    expect(buildTurns(messages)).toEqual([
      { message: messages[0], reasoning: undefined },
      { message: messages[2], reasoning: "thinking" },
    ]);
  });

  it("shows reasoning that arrives before its assistant message", () => {
    const turns = buildTurns([
      { id: "u1", role: "user", content: "Hi" },
      { id: "r1", role: "reasoning", content: "still thinking" },
    ]);
    expect(turns.at(-1)).toEqual({
      message: { id: PENDING_REASONING_ID, role: "assistant", content: "" },
      reasoning: "still thinking",
    });
  });

  it("does not leak reasoning into a later turn", () => {
    const turns = buildTurns([
      { id: "r1", role: "reasoning", content: "first" },
      { id: "a1", role: "assistant", content: "A" },
      { id: "a2", role: "assistant", content: "B" },
    ]);
    expect(turns.map((turn) => turn.reasoning)).toEqual(["first", undefined]);
  });
});

describe("helpers", () => {
  it("finds the tool result for a call", () => {
    const result = { id: "t1", role: "tool", toolCallId: "c1", content: "42" } as const;
    expect(findToolResult([result], "c1")).toBe(result);
    expect(findToolResult([result], "c2")).toBeUndefined();
  });

  it("parses complete tool arguments and keeps partial ones raw", () => {
    expect(parseToolArgs('{"a":1}')).toEqual({ a: 1 });
    expect(parseToolArgs('{"a":')).toBe('{"a":');
  });

  it("returns the latest non-blank line", () => {
    expect(latestLine("one\ntwo\n\n")).toBe("two");
    expect(latestLine("single")).toBe("single");
  });
});
