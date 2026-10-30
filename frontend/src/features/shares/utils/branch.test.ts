import { describe, expect, it } from "vitest";
import type { SharedMessage } from "../api/shares-api";
import { branchRows, latestLeaf } from "./branch";

function message(id: string, parent: string | null, role: string, siblings: string[]): SharedMessage {
  return {
    id,
    parent_message_id: parent,
    role,
    status: "completed",
    content: [],
    created_at: "2026-10-30T00:00:00Z",
    sibling_ids: siblings,
  };
}

// q1 → a1 → q2 → a2, and a regenerated a1b under q1.
const tree = [
  message("q1", null, "user", ["q1"]),
  message("a1", "q1", "assistant", ["a1", "a1b"]),
  message("q2", "a1", "user", ["q2"]),
  message("a2", "q2", "assistant", ["a2"]),
  message("a1b", "q1", "assistant", ["a1", "a1b"]),
];

describe("snapshot branches", () => {
  it("walks from a leaf up to the root", () => {
    expect(branchRows(tree, "a2").map((row) => row.id)).toEqual(["q1", "a1", "q2", "a2"]);
    expect(branchRows(tree, "a1b").map((row) => row.id)).toEqual(["q1", "a1b"]);
  });

  it("continues down the newest children of a chosen version", () => {
    expect(latestLeaf(tree, "a1")).toBe("a2");
    expect(latestLeaf(tree, "a1b")).toBe("a1b");
  });
});
