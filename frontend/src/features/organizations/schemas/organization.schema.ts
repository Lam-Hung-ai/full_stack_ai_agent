import { z } from "zod";
import { nameSchema, newPasswordSchema } from "@/features/auth";

// Mirrors the backend limits for a friendlier message; FastAPI stays the authority.
export const inviteSchema = z.object({
  email: z.email("Email không hợp lệ"),
});

export const roleSchema = z.object({
  name: z.string().trim().min(1, "Nhập tên vai trò").max(200, "Tên quá dài"),
  description: z.string().trim().max(500, "Mô tả quá dài"),
  permissions: z.array(z.string()),
});

/** Account created from an invitation: the email comes from the invitation. */
export const invitationAccountSchema = newPasswordSchema.and(z.object({ name: nameSchema }));

export type InviteValues = z.infer<typeof inviteSchema>;
export type RoleValues = z.infer<typeof roleSchema>;
export type InvitationAccountValues = z.infer<typeof invitationAccountSchema>;
