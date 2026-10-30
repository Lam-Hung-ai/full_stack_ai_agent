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
 * is what follows the question; a resumed turn adds what is new to the row
 * it continues.
 */
export function shownRows(
  saved: readonly RowView[],
  live: LiveTurn | null,
  liveMessages: readonly Message[],
): RowView[] {
  if (!live) return [...saved];
  if (live.continued) {
    const rows = [...live.kept, live.continued];
    const known = new Set(rows.flatMap((row) => row.content.map((message) => message.id)));
    // A resumed stream replays the interrupted tool call under a new id.
    const knownCalls = new Set(
      rows.flatMap((row) =>
        row.content.flatMap((message) =>
          message.role === "tool"
            ? [message.toolCallId]
            : message.role === "assistant"
              ? (message.toolCalls ?? []).map((call) => call.id)
              : [],
        ),
      ),
    );
    const replayed = (message: Message) =>
      (message.role === "tool" && knownCalls.has(message.toolCallId)) ||
      (message.role === "assistant" &&
        !message.content &&
        !!message.toolCalls?.length &&
        message.toolCalls.every((call) => knownCalls.has(call.id)));
    const added = liveMessages.filter(
      (message) => message.role !== "user" && !known.has(message.id) && !replayed(message),
    );
    const answer: RowView = {
      ...live.continued,
      status: live.status,
      content: [...live.continued.content, ...added],
      live: true,
    };
    return [...live.kept, answer];
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
  server_busy: "Hệ thống đang quá tải. Vui lòng gửi lại sau vài giây.",
  invalid_file: "Có tệp đính kèm không dùng được. Hãy bỏ tệp đó rồi gửi lại.",
  too_many_files: "Mỗi câu hỏi đính kèm tối đa 10 tệp.",
  invalid_parent: "Cuộc trò chuyện đã thay đổi. Hãy tải lại trang.",
  parent_required: "Cuộc trò chuyện đã thay đổi. Hãy tải lại trang.",
  message_not_found: "Tin nhắn không còn trong cuộc trò chuyện. Hãy tải lại trang.",
  conversation_not_found: "Không tìm thấy cuộc trò chuyện.",
  not_waiting: "Câu hỏi này đã được trả lời hoặc đã dừng. Hãy tải lại trang.",
  stale_interrupt: "Câu hỏi đã thay đổi. Hãy tải lại trang.",
  resume_incomplete: "Hãy trả lời tất cả câu hỏi của agent.",
  empty_answer: "Câu trả lời không được để trống.",
  permission_denied: "Bạn không còn quyền dùng công cụ này.",
  graph_version_changed: "Agent đã được cập nhật nên không tiếp tục được câu trả lời này. Hãy dừng và hỏi lại.",
  checkpoint_missing: "Không tìm thấy trạng thái đã lưu để tiếp tục. Hãy dừng và hỏi lại.",
  agent_run_failed: "Agent không trả lời được. Vui lòng thử lại.",
  persist_failed: "Không lưu được câu trả lời.",
  network_error: "Mất kết nối. Câu trả lời có thể vẫn đang được tạo; hãy tải lại trang sau ít phút.",
};

export function chatErrorMessage(error: ApiError): string {
  return MESSAGES[error.code] ?? "Đã có lỗi xảy ra. Vui lòng thử lại.";
}
