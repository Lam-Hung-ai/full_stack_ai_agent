"use client";

import { useId } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useLogin } from "../hooks/use-auth-mutations";
import { loginSchema, type LoginValues } from "../schemas/auth.schema";
import { authErrorMessage } from "../utils/error-message";
import { safeNext } from "../utils/safe-next";

export function LoginForm() {
  const id = useId();
  const router = useRouter();
  const next = safeNext(useSearchParams().get("next"));
  const loginMutation = useLogin();
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "", remember: false },
  });
  const { errors } = form.formState;

  const onSubmit = form.handleSubmit((values) =>
    loginMutation.mutate(values, { onSuccess: () => router.replace(next) }),
  );

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>Đăng nhập</CardTitle>
        <CardDescription>Dùng email và mật khẩu của bạn.</CardDescription>
      </CardHeader>
      <CardContent>
        <form noValidate onSubmit={onSubmit}>
          <FieldGroup>
            {loginMutation.isError && (
              <Alert variant="destructive">
                <AlertDescription>{authErrorMessage(loginMutation.error)}</AlertDescription>
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
            <Field data-invalid={!!errors.password}>
              <FieldLabel htmlFor={`${id}-password`}>Mật khẩu</FieldLabel>
              <Input
                autoComplete="current-password"
                id={`${id}-password`}
                type="password"
                aria-invalid={!!errors.password}
                {...form.register("password")}
              />
              <FieldError errors={[errors.password]} />
            </Field>
            <Field orientation="horizontal">
              <Controller
                control={form.control}
                name="remember"
                render={({ field }) => (
                  <Checkbox
                    checked={field.value}
                    id={`${id}-remember`}
                    onCheckedChange={(checked) => field.onChange(checked === true)}
                  />
                )}
              />
              <FieldLabel htmlFor={`${id}-remember`} className="font-normal">
                Ghi nhớ đăng nhập
              </FieldLabel>
            </Field>
            <Button disabled={loginMutation.isPending} type="submit">
              {loginMutation.isPending ? "Đang đăng nhập…" : "Đăng nhập"}
            </Button>
            <p className="text-center text-muted-foreground text-sm">
              Chưa có tài khoản?{" "}
              <Link className="underline underline-offset-4" href="/register">
                Đăng ký
              </Link>
            </p>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  );
}
