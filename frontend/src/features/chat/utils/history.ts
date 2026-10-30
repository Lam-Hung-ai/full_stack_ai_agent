import type { Message } from "@ag-ui/client";
import { ApiError } from "@/lib/api";
import type { LiveTurn, MessageRow, RowView } from "../types/chat.types";

export function toRowView(row: MessageRow): RowView {
  return {
    id: row.id,
    role: row.role,
    status: row.status,
    content: row.content as unknown as Message[],
    siblingIds: row.sibling_ids,
  };
}

export function isActive(row: Pick<MessageRow, "status"> | undefined): boolean {
  return row?.status === "pending" || row?.status === "running";
}

export function isTerminal(row: Pick<MessageRow, "status">): boolean {
  return row.status === "completed" || row.status === "failed" || row.status === "cancelled";
}

/**
 * The rows to draw: the saved branch, or while this tab streams a turn the
 * rows kept above it, the new question and the answer so far. The agent's
 * messages may hold the whole context once a snapshot arrives, so the answer
 * is what follows the question.
 */
export function shownRows(
  saved: readonly RowView[],
  live: LiveTurn | null,
  liveMessages: readonly Message[],
): RowView[] {
  if (!live || (live.done && saved.some((row) => row.id === live.assistantId))) {
    return [...saved];
  }
  const start = liveMessages.findIndex((message) => message.id === live.questionId);
  const answer: RowView = {
    id: live.assistantId ?? "live-assistant",
    role: "assistant",
    status: live.status,
    content: start === -1 ? [] : liveMessages.slice(start + 1),
    siblingIds: [],
    live: true,
  };
  return [...live.kept, ...(live.question ? [live.question] : []), answer];
}

/** The SDK throws `Error & {status, payload}` when the stream request fails. */
export function toChatError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  const failure = error as { status?: number; payload?: { error?: { code?: string } } };
  if (typeof failure?.status === "number") {
    return new ApiError(failure.status, failure.payload?.error?.code ?? "http_error");
  }
  return new ApiError(0, "network_error");
}

const MESSAGES: Record<string, string> = {
  assistant_active: "Câu trả lời trước vẫn đang được tạo. Vui lòng đợi.",
  invalid_parent: "Cuộc trò chuyện đã thay đổi. Hãy tải lại trang.",
  parent_required: "Cuộc trò chuyện đã thay đổi. Hãy tải lại trang.",
  message_not_found: "Tin nhắn không còn trong cuộc trò chuyện. Hãy tải lại trang.",
  conversation_not_found: "Không tìm thấy cuộc trò chuyện.",
  agent_run_failed: "Agent không trả lời được. Vui lòng thử lại.",
  persist_failed: "Không lưu được câu trả lời.",
  network_error: "Mất kết nối. Câu trả lời có thể vẫn đang được tạo; hãy tải lại trang sau ít phút.",
};

export function chatErrorMessage(error: ApiError): string {
  return MESSAGES[error.code] ?? "Đã có lỗi xảy ra. Vui lòng thử lại.";
}
