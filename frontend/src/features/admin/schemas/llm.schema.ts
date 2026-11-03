import { z } from "zod";
import { parseSettings } from "../utils/settings";

// Mirrors the backend rules for friendlier messages; FastAPI stays the authority.
const key = z
  .string()
  .trim()
  .regex(/^[a-z][a-z0-9_-]{0,62}$/, "Chữ thường, số, '-' hoặc '_', bắt đầu bằng chữ");
const name = z.string().trim().min(1, "Nhập tên").max(200, "Tên quá dài");
const settings = z
  .string()
  .refine(
    (text) => parseSettings(text) !== null,
    'Phải là một object JSON, ví dụ {"temperature": 0.2}',
  );

export const connectionSchema = z.object({
  key,
  name,
  provider: z.string().min(1, "Chọn provider"),
  clientParams: settings,
  /** Empty keeps the stored key when editing. */
  apiKey: z.string().trim(),
  clearApiKey: z.boolean(),
  isActive: z.boolean(),
});

export const modelSchema = z.object({
  key,
  name,
  connectionId: z.string().min(1, "Chọn kết nối"),
  model: z.string().trim().min(1, "Nhập tên model của provider").max(200, "Tên quá dài"),
  params: settings,
  isActive: z.boolean(),
});

export type ConnectionValues = z.infer<typeof connectionSchema>;
export type ModelValues = z.infer<typeof modelSchema>;
