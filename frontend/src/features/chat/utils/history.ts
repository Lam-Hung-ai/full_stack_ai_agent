import type { Message } from "@ag-ui/client";
import { ApiError } from "@/lib/api";
import type { MessageRow } from "../types/chat.types";

/** Flatten SQL rows (each an AG-UI bundle) into the SDK's message list. */
export function toAgentMessages(rows: readonly MessageRow[]): Message[] {
  return rows.flatMap((row) => row.content as unknown as Message[]);
}

export function isActive(row: MessageRow | undefined): boolean {
  return row?.status === "pending" || row?.status === "running";
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
  conversation_not_found: "Không tìm thấy cuộc trò chuyện.",
  agent_run_failed: "Agent không trả lời được. Vui lòng thử lại.",
  persist_failed: "Không lưu được câu trả lời.",
  network_error: "Mất kết nối. Câu trả lời có thể vẫn đang được tạo; hãy tải lại trang sau ít phút.",
};

export function chatErrorMessage(error: ApiError): string {
  return MESSAGES[error.code] ?? "Đã có lỗi xảy ra. Vui lòng thử lại.";
}
