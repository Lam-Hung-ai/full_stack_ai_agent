import { z } from "zod";

// Mirrors the backend rules for a friendlier message; FastAPI stays the authority.
export const loginSchema = z.object({
  email: z.email("Email không hợp lệ"),
  password: z.string().min(1, "Nhập mật khẩu"),
  remember: z.boolean(),
});

export const registerSchema = z.object({
  name: z.string().trim().min(1, "Nhập họ tên").max(200),
  email: z.email("Email không hợp lệ"),
  password: z
    .string()
    .min(8, "Mật khẩu tối thiểu 8 ký tự")
    .max(256)
    .regex(/[a-z]/, "Cần ít nhất một chữ thường")
    .regex(/[A-Z]/, "Cần ít nhất một chữ hoa")
    .regex(/\d/, "Cần ít nhất một chữ số")
    .regex(/[^A-Za-z0-9]/, "Cần ít nhất một ký tự đặc biệt"),
});

export type LoginValues = z.infer<typeof loginSchema>;
export type RegisterValues = z.infer<typeof registerSchema>;
