"use client";

import { useId } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useRequestPasswordReset } from "../hooks/use-auth-mutations";
import { forgotPasswordSchema, type ForgotPasswordValues } from "../schemas/auth.schema";
import { authErrorMessage } from "../utils/error-message";

export function ForgotPasswordForm() {
  const id = useId();
  const requestMutation = useRequestPasswordReset();
  const form = useForm<ForgotPasswordValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: "" },
  });
  const { errors } = form.formState;

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>Quên mật khẩu</CardTitle>
        <CardDescription>Nhập email, chúng tôi gửi liên kết đặt mật khẩu mới.</CardDescription>
      </CardHeader>
      <CardContent>
        {requestMutation.isSuccess ? (
          <FieldGroup>
            <Alert>
              <AlertDescription>
                Nếu email này có tài khoản, thư đặt lại mật khẩu đã được gửi. Hãy kiểm tra hộp thư.
              </AlertDescription>
            </Alert>
            <Link className="text-center text-sm underline underline-offset-4" href="/login">
              Quay lại đăng nhập
            </Link>
          </FieldGroup>
        ) : (
          <form
            noValidate
            onSubmit={form.handleSubmit((values) => requestMutation.mutate(values.email))}
          >
            <FieldGroup>
              {requestMutation.isError && (
                <Alert variant="destructive">
                  <AlertDescription>{authErrorMessage(requestMutation.error)}</AlertDescription>
                </Alert>
              )}
              <Field data-invalid={!!errors.email}>
                <FieldLabel htmlFor={`${id}-email`}>Email</FieldLabel>
                <Input
                  autoComplete="email"
                  id={`${id}-email`}
                  type="email"
                  aria-invalid={!!errors.email}
                  {...form.register("email")}
                />
                <FieldError errors={[errors.email]} />
              </Field>
              <Button disabled={requestMutation.isPending} type="submit">
                {requestMutation.isPending ? "Đang gửi…" : "Gửi liên kết"}
              </Button>
              <Link className="text-center text-sm underline underline-offset-4" href="/login">
                Quay lại đăng nhập
              </Link>
            </FieldGroup>
          </form>
        )}
      </CardContent>
    </Card>
  );
}
