import { z } from "zod";

// Mirrors the backend rules for a friendlier message; FastAPI stays the authority.
export const loginSchema = z.object({
  email: z.email("Email không hợp lệ"),
  password: z.string().min(1, "Nhập mật khẩu"),
  remember: z.boolean(),
});

export const passwordSchema = z
  .string()
  .min(8, "Mật khẩu tối thiểu 8 ký tự")
  .max(256)
  .regex(/[a-z]/, "Cần ít nhất một chữ thường")
  .regex(/[A-Z]/, "Cần ít nhất một chữ hoa")
  .regex(/\d/, "Cần ít nhất một chữ số")
  .regex(/[^A-Za-z0-9]/, "Cần ít nhất một ký tự đặc biệt");

export const nameSchema = z.string().trim().min(1, "Nhập họ tên").max(200);

export const registerSchema = z.object({
  name: nameSchema,
  email: z.email("Email không hợp lệ"),
  password: passwordSchema,
});

export const forgotPasswordSchema = z.object({
  email: z.email("Email không hợp lệ"),
});

export const newPasswordSchema = z
  .object({ password: passwordSchema, confirm: z.string() })
  .refine((values) => values.password === values.confirm, {
    path: ["confirm"],
    message: "Mật khẩu nhập lại không khớp",
  });

export type LoginValues = z.infer<typeof loginSchema>;
export type RegisterValues = z.infer<typeof registerSchema>;
export type ForgotPasswordValues = z.infer<typeof forgotPasswordSchema>;
export type NewPasswordValues = z.infer<typeof newPasswordSchema>;
