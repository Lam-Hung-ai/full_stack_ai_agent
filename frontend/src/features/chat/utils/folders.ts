import { ApiError } from "@/lib/api";

export function folderErrorMessage(error: unknown): string {
  return error instanceof ApiError && error.code === "folder_name_taken"
    ? "Đã có folder cùng tên."
    : "Không lưu được folder. Vui lòng thử lại.";
}
