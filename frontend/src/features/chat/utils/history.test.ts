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
  continued: null,
  assistantId: "a1",
  status: "running",
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

  it("adds only what a resumed turn streams to the row it continues", () => {
    const paused: RowView = {
      ...view("a1", "assistant"),
      status: "requires_action",
      content: [
        {
          id: "m1",
          role: "assistant",
          content: "",
          toolCalls: [{ id: "c0", type: "function", function: { name: "clock", arguments: "{}" } }],
        },
        { id: "interaction:x:0", role: "activity", activityType: "user_interaction", content: {} },
      ],
    };
    const messages: Message[] = [
      { id: "u0", role: "user", content: "hỏi" },
      { id: "m1", role: "assistant", content: "" },
      {
        id: "m1-replayed",
        role: "assistant",
        toolCalls: [{ id: "c0", type: "function", function: { name: "clock", arguments: "{}" } }],
      },
      { id: "t1", role: "tool", toolCallId: "c1", content: "CSV" },
      { id: "m2", role: "assistant", content: "Xong" },
    ];
    const rows = shownRows(
      [],
      live({ kept: [view("u0", "user")], question: null, questionId: "", continued: paused }),
      messages,
    );
    expect(rows.map((r) => r.id)).toEqual(["u0", "a1"]);
    expect(rows[1].content.map((m) => m.id)).toEqual(["m1", "interaction:x:0", "t1", "m2"]);
  });

  it("returns the saved branch when nothing streams", () => {
    const saved = [view("u0", "user"), view("a0", "assistant")];
    expect(shownRows(saved, null, [])).toEqual(saved);
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
