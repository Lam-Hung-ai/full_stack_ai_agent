import type { Message } from "@ag-ui/client";
import { describe, expect, it } from "vitest";
import { ApiError } from "@/lib/api";
import type { LiveTurn, MessageRow, RowView } from "../types/chat.types";
import { chatErrorMessage, isActive, shownRows, toChatError, toRowView } from "./history";

const row = (overrides: Partial<MessageRow>): MessageRow => ({
  id: "r",
  parent_message_id: null,
  role: "assistant",
  status: "completed",
  content: [],
  created_at: "2026-10-30T00:00:00Z",
  sibling_ids: ["r"],
  ...overrides,
});

const view = (id: string, role: RowView["role"]): RowView => ({
  id,
  role,
  status: "completed",
  content: [],
  siblingIds: [id],
});

const live = (overrides: Partial<LiveTurn>): LiveTurn => ({
  kept: [view("u0", "user"), view("a0", "assistant")],
  question: view("u1", "user"),
  questionId: "u1",
  assistantId: "a1",
  status: "running",
  done: false,
  ...overrides,
});

describe("history", () => {
  it("keeps each row's bundle and branch siblings", () => {
    const shown = toRowView(
      row({
        id: "a",
        sibling_ids: ["a0", "a"],
        content: [
          { id: "r1", role: "reasoning", content: "nghĩ" },
          { id: "m1", role: "assistant", content: "đáp" },
        ],
      }),
    );
    expect(shown.content.map((message) => message.id)).toEqual(["r1", "m1"]);
    expect(shown.siblingIds).toEqual(["a0", "a"]);
  });

  it("draws the live answer after its question, ignoring snapshot context", () => {
    const messages: Message[] = [
      { id: "old", role: "user", content: "trước" },
      { id: "u1", role: "user", content: "hỏi" },
      { id: "m1", role: "assistant", content: "đáp" },
    ];
    const rows = shownRows([view("u0", "user")], live({}), messages);
    expect(rows.map((r) => r.id)).toEqual(["u0", "a0", "u1", "a1"]);
    expect(rows.at(-1)?.content.map((m) => m.id)).toEqual(["m1"]);
    expect(rows.at(-1)?.live).toBe(true);
  });

  it("returns to the saved branch once it holds the finished answer", () => {
    const saved = [view("u0", "user"), view("a0", "assistant"), view("u1", "user"), view("a1", "assistant")];
    expect(shownRows(saved, live({ done: true }), [])).toEqual(saved);
    // Not yet refetched: the live turn stays on screen.
    expect(shownRows(saved.slice(0, 2), live({ done: true }), []).at(-1)?.live).toBe(true);
  });

  it("knows when a turn is still running", () => {
    expect(isActive(row({ status: "running" }))).toBe(true);
    expect(isActive(row({ status: "failed" }))).toBe(false);
    expect(isActive(undefined)).toBe(false);
  });

  it("turns SDK stream errors into ApiError", () => {
    const error = toChatError({ status: 409, payload: { error: { code: "assistant_active" } } });
    expect(error).toMatchObject({ status: 409, code: "assistant_active" });
    expect(toChatError(new TypeError("Failed to fetch"))).toMatchObject({ code: "network_error" });
    expect(chatErrorMessage(new ApiError(409, "assistant_active"))).toContain("đang được tạo");
  });
});
