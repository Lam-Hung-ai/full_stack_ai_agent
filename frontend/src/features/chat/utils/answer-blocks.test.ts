import type { Message as AGUIMessage } from "@ag-ui/client";
import { describe, expect, it } from "vitest";
import { answerBlocks, answerCopyText, workSummary } from "./answer-blocks";

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

describe("workSummary", () => {
  const base = {
    running: false,
    elapsed: 0,
    status: "completed" as const,
    workTime: "33 giây",
    isFirst: true,
    isLast: true,
  };

  it("counts while running and tells how a finished row ended", () => {
    expect(workSummary({ ...base, running: true, workTime: null })).toBe("Đang làm việc…");
    expect(workSummary({ ...base, running: true, elapsed: 12 })).toBe("Đang làm việc… 12 giây");
    expect(workSummary(base)).toBe("Đã làm việc trong 33 giây");
    expect(workSummary({ ...base, status: "cancelled" })).toBe("Đã dừng sau 33 giây");
    expect(workSummary({ ...base, status: "failed", workTime: null })).toBe("Gặp lỗi");
  });

  it("puts the duration on the first run and the ending on the last", () => {
    expect(workSummary({ ...base, isFirst: false })).toBe("Đã làm việc");
    expect(workSummary({ ...base, status: "cancelled", isLast: false })).toBe("Đã làm việc");
    expect(workSummary({ ...base, status: "requires_action", workTime: null })).toBe("Đã làm việc");
  });
});
