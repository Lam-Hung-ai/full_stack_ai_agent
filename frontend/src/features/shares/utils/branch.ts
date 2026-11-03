import type { RowView } from "@/features/chat";
import type { SharedTurn } from "../api/shares-api";

/**
 * The branch of a snapshot that ends at `leafId`, root first. Switching to
 * another version continues down its newest children, as the chat does.
 */
export function branchRows(turns: readonly SharedTurn[], leafId: string): RowView[] {
  const byId = new Map(turns.map((turn) => [turn.id, turn]));
  const rows: RowView[] = [];
  for (let turn = byId.get(leafId); turn; ) {
    rows.unshift({
      id: turn.id,
      role: turn.role as RowView["role"],
      status: turn.status as RowView["status"],
      content: turn.content as unknown as RowView["content"],
      siblingIds: turn.sibling_ids,
      createdAt: turn.created_at,
    });
    turn = turn.parent_turn_id ? byId.get(turn.parent_turn_id) : undefined;
  }
  return rows;
}

/** Follow the newest child down from a turn to the end of its branch. */
export function latestLeaf(turns: readonly SharedTurn[], turnId: string): string {
  let leaf = turnId;
  for (;;) {
    const children = turns.filter((turn) => turn.parent_turn_id === leaf);
    if (children.length === 0) return leaf;
    leaf = children[children.length - 1].id;
  }
}
