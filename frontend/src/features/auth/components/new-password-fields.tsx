"use client";

import type { UseFormReturn } from "react-hook-form";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";

type PasswordPair = { password: string; confirm: string };

/** A new password typed twice; shared by password reset and invitations. */
export function NewPasswordFields<T extends PasswordPair>({
  form,
  idPrefix,
}: {
  form: UseFormReturn<T>;
  idPrefix: string;
}) {
  // The generic form only ever carries these two string fields here.
  const pair = form as unknown as UseFormReturn<PasswordPair>;
  const { errors } = pair.formState;
  return (
    <>
      <Field data-invalid={!!errors.password}>
        <FieldLabel htmlFor={`${idPrefix}-password`}>Mật khẩu mới</FieldLabel>
        <Input
          autoComplete="new-password"
          id={`${idPrefix}-password`}
          type="password"
          aria-invalid={!!errors.password}
          {...pair.register("password")}
        />
        <FieldError errors={[errors.password]} />
      </Field>
      <Field data-invalid={!!errors.confirm}>
        <FieldLabel htmlFor={`${idPrefix}-confirm`}>Nhập lại mật khẩu</FieldLabel>
        <Input
          autoComplete="new-password"
          id={`${idPrefix}-confirm`}
          type="password"
          aria-invalid={!!errors.confirm}
          {...pair.register("confirm")}
        />
        <FieldError errors={[errors.confirm]} />
      </Field>
    </>
  );
}
