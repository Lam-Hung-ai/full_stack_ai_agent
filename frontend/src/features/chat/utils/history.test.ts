import { describe, expect, it } from "vitest";
import { ApiError } from "@/lib/api";
import type { MessageRow } from "../types/chat.types";
import { chatErrorMessage, isActive, toAgentMessages, toChatError } from "./history";

const row = (overrides: Partial<MessageRow>): MessageRow => ({
  id: "r",
  parent_message_id: null,
  role: "assistant",
  status: "completed",
  content: [],
  created_at: "2026-10-30T00:00:00Z",
  ...overrides,
});

describe("history", () => {
  it("flattens bundles in branch order", () => {
    const messages = toAgentMessages([
      row({ role: "user", content: [{ id: "u", role: "user", content: "hỏi" }] }),
      row({
        content: [
          { id: "r1", role: "reasoning", content: "nghĩ" },
          { id: "a1", role: "assistant", content: "đáp" },
        ],
      }),
    ]);
    expect(messages.map((message) => message.id)).toEqual(["u", "r1", "a1"]);
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
