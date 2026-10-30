"use client";

import { useId } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FieldGroup } from "@/components/ui/field";
import { useResetPassword } from "../hooks/use-auth-mutations";
import { newPasswordSchema, type NewPasswordValues } from "../schemas/auth.schema";
import { authErrorMessage } from "../utils/error-message";
import { NewPasswordFields } from "./new-password-fields";

export function ResetPasswordForm() {
  const id = useId();
  const token = useSearchParams().get("token") ?? "";
  const resetMutation = useResetPassword();
  const form = useForm<NewPasswordValues>({
    resolver: zodResolver(newPasswordSchema),
    defaultValues: { password: "", confirm: "" },
  });

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>Đặt mật khẩu mới</CardTitle>
        <CardDescription>Mọi phiên đăng nhập đang mở sẽ bị đăng xuất.</CardDescription>
      </CardHeader>
      <CardContent>
        {resetMutation.isSuccess ? (
          <FieldGroup>
            <Alert>
              <AlertDescription>Đã đặt mật khẩu mới.</AlertDescription>
            </Alert>
            <Button asChild>
              <Link href="/login">Đăng nhập</Link>
            </Button>
          </FieldGroup>
        ) : (
          <form
            noValidate
            onSubmit={form.handleSubmit((values) =>
              resetMutation.mutate({ token, password: values.password }),
            )}
          >
            <FieldGroup>
              {(resetMutation.isError || !token) && (
                <Alert variant="destructive">
                  <AlertDescription>
                    {authErrorMessage(resetMutation.error ?? { code: "invalid_token" })}
                  </AlertDescription>
                </Alert>
              )}
              <NewPasswordFields form={form} idPrefix={id} />
              <Button disabled={resetMutation.isPending || !token} type="submit">
                {resetMutation.isPending ? "Đang lưu…" : "Đặt mật khẩu"}
              </Button>
              <Link
                className="text-center text-sm underline underline-offset-4"
                href="/forgot-password"
              >
                Gửi lại liên kết
              </Link>
            </FieldGroup>
          </form>
        )}
      </CardContent>
    </Card>
  );
}
