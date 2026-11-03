import { z } from "zod";

// Mirrors the backend limits for a friendlier message; FastAPI stays the authority.
export const questionSchema = z.object({
  text: z.string().trim().min(1, "Nhập câu hỏi").max(32_000, "Câu hỏi quá dài"),
});

export const answerSchema = z.object({
  answer: z.string().trim().min(1, "Nhập câu trả lời").max(4_000, "Câu trả lời quá dài"),
});

export type AnswerValues = z.infer<typeof answerSchema>;
export type QuestionValues = z.infer<typeof questionSchema>;
