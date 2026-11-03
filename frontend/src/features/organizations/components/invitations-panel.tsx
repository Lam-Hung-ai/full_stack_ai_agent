"use client";

import { useId } from "react";
import { RotateCwIcon, XIcon } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useInvitations, useOrganizationActions } from "../hooks/use-organization";
import { inviteSchema, type InviteValues } from "../schemas/organization.schema";
import { organizationErrorMessage } from "../utils/error-message";

const dateFormat = new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium" });

export function InvitationsPanel({ organizationId }: { organizationId: string }) {
  const id = useId();
  const invitations = useInvitations(organizationId);
  const { invite, revokeInvitation } = useOrganizationActions(organizationId);
  const form = useForm<InviteValues>({
    resolver: zodResolver(inviteSchema),
    defaultValues: { email: "" },
  });
  const { errors } = form.formState;
  const error = invite.error ?? revokeInvitation.error;

  return (
    <div className="flex flex-col gap-4">
      <form
        className="flex items-end gap-2"
        noValidate
        onSubmit={form.handleSubmit((values) =>
          invite.mutate(values.email, { onSuccess: () => form.reset() }),
        )}
      >
        <Field className="flex-1" data-invalid={!!errors.email}>
          <FieldLabel htmlFor={`${id}-email`}>Mời bằng email</FieldLabel>
          <Input
            aria-invalid={!!errors.email}
            id={`${id}-email`}
            placeholder="ten@congty.vn"
            type="email"
            {...form.register("email")}
          />
          <FieldError errors={[errors.email]} />
        </Field>
        <Button disabled={invite.isPending} type="submit">
          Gửi lời mời
        </Button>
      </form>
      <p className="text-muted-foreground text-sm">
        Người được mời vào với vai trò Thành viên; đổi vai trò sau khi họ tham gia.
      </p>
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{organizationErrorMessage(error)}</AlertDescription>
        </Alert>
      )}
      {invitations.isPending ? (
        <Spinner aria-label="Đang tải lời mời" />
      ) : invitations.data?.data.length ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Email</TableHead>
              <TableHead>Người mời</TableHead>
              <TableHead>Hết hạn</TableHead>
              <TableHead className="w-24" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {invitations.data.data.map((invitation) => (
              <TableRow key={invitation.id}>
                <TableCell>{invitation.email}</TableCell>
                <TableCell>{invitation.invited_by_name}</TableCell>
                <TableCell>{dateFormat.format(new Date(invitation.expires_at))}</TableCell>
                <TableCell>
                  <div className="flex justify-end gap-1">
                    <Button
                      aria-label={`Gửi lại lời mời cho ${invitation.email}`}
                      disabled={invite.isPending}
                      onClick={() => invite.mutate(invitation.email)}
                      size="icon"
                      variant="ghost"
                    >
                      <RotateCwIcon />
                    </Button>
                    <Button
                      aria-label={`Thu hồi lời mời của ${invitation.email}`}
                      disabled={revokeInvitation.isPending}
                      onClick={() => revokeInvitation.mutate(invitation.id)}
                      size="icon"
                      variant="ghost"
                    >
                      <XIcon />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <p className="text-muted-foreground text-sm">Không có lời mời nào đang chờ.</p>
      )}
    </div>
  );
}
