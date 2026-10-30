import { ApiError } from "@/lib/api";

const MESSAGES: Record<string, string> = {
  permission_denied: "Bạn không có quyền làm việc này.",
  permission_escalation: "Bạn không thể cấp quyền mà chính bạn không có.",
  owner_required: "Chỉ chủ sở hữu mới thay đổi được vai trò chủ sở hữu.",
  last_owner: "Tổ chức cần ít nhất một chủ sở hữu. Hãy chuyển quyền chủ sở hữu trước.",
  already_member: "Người này đã là thành viên.",
  role_name_taken: "Tên vai trò đã được dùng.",
  role_locked: "Vai trò có sẵn không đổi được tên hoặc xoá; vai trò chủ sở hữu luôn đủ quyền.",
  unknown_role: "Vai trò không còn tồn tại. Tải lại trang rồi thử lại.",
  member_not_found: "Thành viên không còn trong tổ chức.",
  invitation_not_found: "Lời mời không tồn tại.",
  invitation_expired: "Lời mời đã hết hạn. Hãy nhờ quản trị viên gửi lại.",
  invitation_revoked: "Lời mời đã bị thu hồi hoặc thay bằng lời mời mới.",
  invitation_accepted: "Lời mời đã được dùng.",
  invitation_email_mismatch: "Lời mời gửi cho email khác với tài khoản đang đăng nhập.",
  email_exists: "Email này đã có tài khoản. Hãy đăng nhập để nhận lời mời.",
  organization_not_found: "Tổ chức không tồn tại hoặc bạn không còn là thành viên.",
  rate_limited: "Bạn thử quá nhiều lần. Vui lòng đợi một phút.",
  network_error: "Không kết nối được máy chủ.",
};

export function organizationErrorMessage(error: unknown): string {
  if (error instanceof ApiError && MESSAGES[error.code]) return MESSAGES[error.code];
  return "Đã có lỗi xảy ra. Vui lòng thử lại.";
}
