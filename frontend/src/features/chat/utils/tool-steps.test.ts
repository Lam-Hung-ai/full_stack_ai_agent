import { describe, expect, it } from "vitest";
import type { WorkStep } from "./answer-blocks";
import { toolResultText, workDone } from "./tool-steps";

const tool = (id: string, name: string, result?: { content: string; error?: string }) =>
  ({
    kind: "tool",
    id,
    call: { id, type: "function", function: { name, arguments: "{}" } },
    result: result && { id: `r-${id}`, role: "tool", toolCallId: id, ...result },
  }) as WorkStep & { kind: "tool" };

describe("workDone", () => {
  it("says what the tools did, counted, in their order", () => {
    const steps: WorkStep[] = [
      { kind: "thinking", id: "t", text: "…" },
      tool("1", "get_current_time"),
      tool("2", "create_file"),
      tool("3", "create_file"),
      tool("4", "search_web"),
    ];
    expect(workDone(steps)).toBe("xem giờ, tạo 2 tệp, search_web");
    expect(workDone([{ kind: "thinking", id: "t", text: "…" }])).toBe("suy nghĩ");
  });
});

describe("toolResultText", () => {
  it("reads a time, a made file, a short result and an error", () => {
    const clock = toolResultText(
      tool("1", "get_current_time", { content: "2026-11-03T02:40:23Z" }),
    );
    expect(clock?.text).toMatch(/2026/);
    const file = toolResultText(
      tool("2", "create_file", {
        content: JSON.stringify({ file_id: "f", name: "báo cáo.xlsx", size_bytes: 2048 }),
      }),
    );
    expect(file).toEqual({ text: "báo cáo.xlsx · 2.0 KB", isError: false });
    expect(toolResultText(tool("3", "lookup", { content: "Hà Nội" }))?.text).toBe("Hà Nội");
    expect(toolResultText(tool("4", "lookup", { content: "x".repeat(200) }))).toBeNull();
    expect(
      toolResultText(tool("5", "create_file", { content: "", error: "Hết dung lượng" })),
    ).toEqual({
      text: "Hết dung lượng",
      isError: true,
    });
    expect(toolResultText(tool("6", "create_file"))).toBeNull();
  });
});
