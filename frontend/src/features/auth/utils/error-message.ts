import { ApiError } from "@/lib/api";

const MESSAGES: Record<string, string> = {
  invalid_credentials: "Email hoặc mật khẩu không đúng.",
  email_exists: "Email này đã có tài khoản.",
  registration_disabled: "Hệ thống chưa mở đăng ký tài khoản.",
  rate_limited: "Bạn thử quá nhiều lần. Vui lòng đợi một phút.",
  network_error: "Không kết nối được máy chủ.",
};

export function authErrorMessage(error: unknown): string {
  if (error instanceof ApiError && MESSAGES[error.code]) return MESSAGES[error.code];
  return "Đã có lỗi xảy ra. Vui lòng thử lại.";
}
