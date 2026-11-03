"use client";

import { useId } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useLogin, useRegister } from "../hooks/use-auth-mutations";
import { registerSchema, type RegisterValues } from "../schemas/auth.schema";
import { authErrorMessage } from "../utils/error-message";

export function RegisterForm() {
  const id = useId();
  const router = useRouter();
  const registerMutation = useRegister();
  const loginMutation = useLogin();
  const form = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { name: "", email: "", password: "" },
  });
  const { errors } = form.formState;
  const pending = registerMutation.isPending || loginMutation.isPending;
  const failure = registerMutation.error ?? loginMutation.error;

  const onSubmit = form.handleSubmit(async (values) => {
    await registerMutation.mutateAsync(values);
    await loginMutation.mutateAsync({
      email: values.email,
      password: values.password,
      remember: false,
    });
    router.replace("/");
  });

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>Tạo tài khoản</CardTitle>
        <CardDescription>Bạn có một không gian làm việc cá nhân ngay sau khi đăng ký.</CardDescription>
      </CardHeader>
      <CardContent>
        <form noValidate onSubmit={(event) => void onSubmit(event).catch(() => undefined)}>
          <FieldGroup>
            {failure && (
              <Alert variant="destructive">
                <AlertDescription>{authErrorMessage(failure)}</AlertDescription>
              </Alert>
            )}
            <Field data-invalid={!!errors.name}>
              <FieldLabel htmlFor={`${id}-name`}>Họ tên</FieldLabel>
              <Input autoComplete="name" id={`${id}-name`} aria-invalid={!!errors.name} {...form.register("name")} />
              <FieldError errors={[errors.name]} />
            </Field>
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
                autoComplete="new-password"
                id={`${id}-password`}
                type="password"
                aria-invalid={!!errors.password}
                {...form.register("password")}
              />
              <FieldError errors={[errors.password]} />
            </Field>
            <Button disabled={pending} type="submit">
              {pending ? "Đang tạo tài khoản…" : "Đăng ký"}
            </Button>
            <p className="text-center text-muted-foreground text-sm">
              Đã có tài khoản?{" "}
              <Link className="underline underline-offset-4" href="/login">
                Đăng nhập
              </Link>
            </p>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  );
}
