"use client";

import { useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Spinner } from "@/components/ui/spinner";
import { useOrganizationActions, useRoles } from "../hooks/use-organization";
import type { Member } from "../types/organization.types";
import { organizationErrorMessage } from "../utils/error-message";
import { roleLabel } from "../utils/permissions";

/** Pick the member's roles; mounted only while open. */
export function MemberRolesDialog({
  organizationId,
  member,
  onClose,
}: {
  organizationId: string;
  member: Member;
  onClose: () => void;
}) {
  const roles = useRoles(organizationId);
  const { updateMemberRoles } = useOrganizationActions(organizationId);
  const [selected, setSelected] = useState(() => new Set(member.roles.map((role) => role.id)));

  const toggle = (roleId: string, checked: boolean) =>
    setSelected((current) => {
      const next = new Set(current);
      if (checked) next.add(roleId);
      else next.delete(roleId);
      return next;
    });

  return (
    <Dialog onOpenChange={(open) => !open && onClose()} open>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Vai trò của {member.name}</DialogTitle>
          <DialogDescription>Quyền của thành viên là hợp các vai trò được chọn.</DialogDescription>
        </DialogHeader>
        {updateMemberRoles.isError && (
          <Alert variant="destructive">
            <AlertDescription>{organizationErrorMessage(updateMemberRoles.error)}</AlertDescription>
          </Alert>
        )}
        {roles.isPending ? (
          <Spinner aria-label="Đang tải vai trò" />
        ) : (
          <FieldGroup className="gap-3">
            {roles.data?.data.map((role) => (
              <Field key={role.id} orientation="horizontal">
                <Checkbox
                  checked={selected.has(role.id)}
                  id={`role-${role.id}`}
                  onCheckedChange={(checked) => toggle(role.id, checked === true)}
                />
                <FieldLabel className="font-normal" htmlFor={`role-${role.id}`}>
                  {roleLabel(role)}
                </FieldLabel>
              </Field>
            ))}
          </FieldGroup>
        )}
        <DialogFooter>
          <Button onClick={onClose} variant="ghost">
            Huỷ
          </Button>
          <Button
            disabled={selected.size === 0 || updateMemberRoles.isPending}
            onClick={() =>
              updateMemberRoles.mutate(
                { memberId: member.id, roleIds: [...selected] },
                { onSuccess: onClose },
              )
            }
          >
            Lưu
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
