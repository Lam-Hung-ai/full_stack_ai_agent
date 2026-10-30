"use client";

import { useId } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { NewPasswordFields, useLogin, useLogout, useSession } from "@/features/auth";
import { useSelectWorkspace } from "@/features/workspaces";
import {
  useAcceptInvitation,
  useInvitationPreview,
  useRegisterWithInvitation,
} from "../hooks/use-invitation";
import {
  invitationAccountSchema,
  type InvitationAccountValues,
} from "../schemas/organization.schema";
import type { InvitationPreview, JoinedOrganization } from "../types/organization.types";
import { organizationErrorMessage } from "../utils/error-message";

const CLOSED: Record<string, string> = {
  accepted: "Lời mời này đã được dùng.",
  revoked: "Lời mời đã bị thu hồi hoặc thay bằng lời mời mới.",
  expired: "Lời mời đã hết hạn. Hãy nhờ quản trị viên gửi lại.",
};

/** Opened from an invitation letter, signed in or not. */
export function InvitationScreen() {
  const token = useSearchParams().get("token") ?? "";
  const preview = useInvitationPreview(token);
  const session = useSession();

  let content: React.ReactNode;
  if (!token || preview.isError) {
    content = (
      <Problem
        message={
          token ? organizationErrorMessage(preview.error) : "Liên kết mời không hợp lệ."
        }
      />
    );
  } else if (preview.isPending || session.isPending) {
    content = (
      <div className="flex justify-center" aria-busy="true">
        <Spinner aria-label="Đang tải lời mời" />
      </div>
    );
  } else if (preview.data.status !== "pending") {
    content = <Problem message={CLOSED[preview.data.status]} />;
  } else if (session.isSuccess) {
    content = (
      <SignedIn email={session.data.user.email} invitation={preview.data} token={token} />
    );
  } else if (preview.data.account_exists) {
    const next = `/invitations?token=${encodeURIComponent(token)}`;
    content = (
      <FieldGroup>
        <p className="text-sm">
          Đăng nhập bằng <strong>{preview.data.email}</strong> để nhận lời mời.
        </p>
        <Button asChild>
          <Link href={`/login?next=${encodeURIComponent(next)}`}>Đăng nhập</Link>
        </Button>
      </FieldGroup>
    );
  } else {
    content = <CreateAccount invitation={preview.data} token={token} />;
  }

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>Lời mời tham gia tổ chức</CardTitle>
        {preview.data && (
          <CardDescription>
            Bạn được mời vào <strong>{preview.data.organization_name}</strong>.
          </CardDescription>
        )}
      </CardHeader>
      <CardContent>{content}</CardContent>
    </Card>
  );
}

function Problem({ message }: { message: string }) {
  return (
    <FieldGroup>
      <Alert variant="destructive">
        <AlertDescription>{message}</AlertDescription>
      </Alert>
      <Button asChild variant="outline">
        <Link href="/">Vào ứng dụng</Link>
      </Button>
    </FieldGroup>
  );
}

/** After joining, work in the organization's workspace. */
function useEnterOrganization() {
  const router = useRouter();
  const selectWorkspace = useSelectWorkspace();
  return (joined: JoinedOrganization) => {
    selectWorkspace(joined.workspace_id);
    router.replace("/");
  };
}

function SignedIn({
  token,
  email,
  invitation,
}: {
  token: string;
  email: string;
  invitation: InvitationPreview;
}) {
  const acceptMutation = useAcceptInvitation();
  const logoutMutation = useLogout();
  const enter = useEnterOrganization();

  if (email.toLowerCase() !== invitation.email.toLowerCase()) {
    return (
      <FieldGroup>
        <Alert variant="destructive">
          <AlertDescription>
            Lời mời gửi cho {invitation.email}, nhưng bạn đang đăng nhập bằng {email}.
          </AlertDescription>
        </Alert>
        <Button
          disabled={logoutMutation.isPending}
          // Start over signed out: clearing the cache does not refetch the
          // queries this page is showing.
          onClick={() =>
            logoutMutation.mutate(undefined, { onSettled: () => window.location.reload() })
          }
          variant="outline"
        >
          Đăng xuất để đổi tài khoản
        </Button>
      </FieldGroup>
    );
  }
  return (
    <FieldGroup>
      {acceptMutation.isError && (
        <Alert variant="destructive">
          <AlertDescription>{organizationErrorMessage(acceptMutation.error)}</AlertDescription>
        </Alert>
      )}
      <Button
        disabled={acceptMutation.isPending}
        onClick={() => acceptMutation.mutate(token, { onSuccess: enter })}
      >
        {acceptMutation.isPending ? "Đang tham gia…" : "Nhận lời mời"}
      </Button>
    </FieldGroup>
  );
}

function CreateAccount({ token, invitation }: { token: string; invitation: InvitationPreview }) {
  const id = useId();
  const registerMutation = useRegisterWithInvitation();
  const loginMutation = useLogin();
  const enter = useEnterOrganization();
  const form = useForm<InvitationAccountValues>({
    resolver: zodResolver(invitationAccountSchema),
    defaultValues: { name: "", password: "", confirm: "" },
  });
  const { errors } = form.formState;
  const failure = registerMutation.error ?? loginMutation.error;

  const onSubmit = form.handleSubmit(async (values) => {
    // Once the account exists (the invitation is used), a retry only logs in.
    const joined =
      registerMutation.data ??
      (await registerMutation.mutateAsync({
        token,
        name: values.name,
        password: values.password,
      }));
    await loginMutation.mutateAsync({
      email: invitation.email,
      password: values.password,
      remember: false,
    });
    enter(joined);
  });

  return (
    <form noValidate onSubmit={(event) => void onSubmit(event).catch(() => undefined)}>
      <FieldGroup>
        <p className="text-sm">
          Tạo tài khoản cho <strong>{invitation.email}</strong> để tham gia.
        </p>
        {failure && (
          <Alert variant="destructive">
            <AlertDescription>{organizationErrorMessage(failure)}</AlertDescription>
          </Alert>
        )}
        <Field data-invalid={!!errors.name}>
          <FieldLabel htmlFor={`${id}-name`}>Họ tên</FieldLabel>
          <Input
            autoComplete="name"
            aria-invalid={!!errors.name}
            id={`${id}-name`}
            {...form.register("name")}
          />
          <FieldError errors={[errors.name]} />
        </Field>
        <NewPasswordFields form={form} idPrefix={id} />
        <Button disabled={registerMutation.isPending || loginMutation.isPending} type="submit">
          Tạo tài khoản và tham gia
        </Button>
      </FieldGroup>
    </form>
  );
}
