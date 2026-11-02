import { ApiError } from "@/lib/api";

const MESSAGES: Record<string, string> = {
  superuser_required: "Chỉ quản trị viên hệ thống mới vào được trang này.",
  llm_key_taken: "Mã này đã được dùng.",
  unknown_provider: "Provider không có trong init_chat_model của LangChain.",
  provider_not_installed: "Máy chủ chưa cài package của provider này.",
  secret_in_settings: "Tham số không được chứa khoá bí mật; hãy nhập vào ô API key.",
  llm_encryption_unavailable: "Máy chủ chưa đặt LLM_ENCRYPTION_KEY hoặc khoá không đúng.",
  connection_in_use: "Kết nối đang được model dùng. Xoá hoặc chuyển các model đó trước.",
  model_in_use: "Model đang được gán. Bỏ gán trước khi xoá.",
  connection_not_found: "Kết nối không còn tồn tại. Tải lại trang.",
  model_not_found: "Model không còn tồn tại. Tải lại trang.",
  duplicate_model: "Mỗi model chỉ được gán một lần cho một mục đích.",
  nothing_to_update: "Không có gì thay đổi.",
  network_error: "Không kết nối được máy chủ.",
};

export function llmErrorMessage(error: unknown): string {
  if (error instanceof ApiError && MESSAGES[error.code]) return MESSAGES[error.code];
  if (error instanceof ApiError && error.status === 422) return "Dữ liệu chưa hợp lệ.";
  return "Đã có lỗi xảy ra. Vui lòng thử lại.";
}
