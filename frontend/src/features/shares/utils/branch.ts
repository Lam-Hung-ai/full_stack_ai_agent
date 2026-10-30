import type { RowView } from "@/features/chat";
import type { SharedMessage } from "../api/shares-api";

/**
 * The branch of a snapshot that ends at `leafId`, root first. Switching to
 * another version continues down its newest children, as the chat does.
 */
export function branchRows(messages: readonly SharedMessage[], leafId: string): RowView[] {
  const byId = new Map(messages.map((message) => [message.id, message]));
  const rows: RowView[] = [];
  for (let message = byId.get(leafId); message; ) {
    rows.unshift({
      id: message.id,
      role: message.role as RowView["role"],
      status: message.status as RowView["status"],
      content: message.content as unknown as RowView["content"],
      siblingIds: message.sibling_ids,
    });
    message = message.parent_message_id ? byId.get(message.parent_message_id) : undefined;
  }
  return rows;
}

/** Follow the newest child down from a message to the end of its branch. */
export function latestLeaf(messages: readonly SharedMessage[], messageId: string): string {
  let leaf = messageId;
  for (;;) {
    const children = messages.filter((message) => message.parent_message_id === leaf);
    if (children.length === 0) return leaf;
    leaf = children[children.length - 1].id;
  }
}
