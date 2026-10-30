import { z } from "zod";

// Mirrors the backend limits for a friendlier message; FastAPI stays the authority.
export const questionSchema = z.object({
  text: z.string().trim().min(1, "Nhập câu hỏi").max(32_000, "Câu hỏi quá dài"),
});

export const nameSchema = z.object({
  name: z.string().trim().min(1, "Nhập tên").max(200, "Tên quá dài"),
});

export type QuestionValues = z.infer<typeof questionSchema>;
export type NameValues = z.infer<typeof nameSchema>;
