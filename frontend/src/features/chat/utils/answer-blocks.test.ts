import type { Message as AGUIMessage } from "@ag-ui/client";
import { describe, expect, it } from "vitest";
import { answerBlocks, answerCopyText } from "./answer-blocks";

const call = (id: string, name: string) => ({
  id,
  type: "function" as const,
  function: { name, arguments: "{}" },
});

describe("answerBlocks", () => {
  it("puts thinking, tools and the text between them in one work block", () => {
    const messages = [
      { id: "r1", role: "reasoning", content: "Cần xem giờ" },
      {
        id: "a1",
        role: "assistant",
        content: "Để mình xem giờ.",
        toolCalls: [call("c1", "get_current_time")],
      },
      { id: "t1", role: "tool", content: "10:00", toolCallId: "c1" },
      { id: "r2", role: "reasoning", content: "Đã có giờ" },
      { id: "a2", role: "assistant", content: "Bây giờ là 10:00." },
    ] as AGUIMessage[];
    const blocks = answerBlocks(messages);
    expect(blocks.map((block) => block.kind)).toEqual(["work", "text"]);
    const work = blocks[0];
    expect(work.kind === "work" && work.steps.map((step) => step.kind)).toEqual([
      "thinking",
      "note",
      "tool",
      "thinking",
    ]);
    expect(
      work.kind === "work" && work.steps[2].kind === "tool" && work.steps[2].result?.content,
    ).toBe("10:00");
    expect(answerCopyText(blocks)).toBe("Bây giờ là 10:00.");
  });

  it("splits work around a question to the user and keeps a plain answer as text", () => {
    const messages = [
      { id: "r1", role: "reasoning", content: "Thiếu thông tin" },
      { id: "a1", role: "assistant", content: "", toolCalls: [call("c1", "ask_user")] },
      { id: "q1", role: "activity", activityType: "interaction", content: {} },
      { id: "r2", role: "reasoning", content: "Đã đủ" },
      { id: "a2", role: "assistant", content: "Xong." },
    ] as unknown as AGUIMessage[];
    expect(answerBlocks(messages).map((block) => block.kind)).toEqual([
      "work",
      "activity",
      "work",
      "text",
    ]);
    expect(
      answerBlocks([{ id: "a", role: "assistant", content: "Chào" }] as AGUIMessage[]),
    ).toEqual([{ kind: "text", id: "a", text: "Chào" }]);
  });
});
