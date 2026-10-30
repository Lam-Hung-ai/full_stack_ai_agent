"use client";

import { useState } from "react";
import { LockIcon, PencilIcon, PlusIcon, Trash2Icon } from "lucide-react";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useOrganizationActions, usePermissions, useRoles } from "../hooks/use-organization";
import type { RoleValues } from "../schemas/organization.schema";
import type { Organization, Role } from "../types/organization.types";
import { organizationErrorMessage } from "../utils/error-message";
import { roleLabel } from "../utils/permissions";
import { RoleDialog } from "./role-dialog";

type Editing = { mode: "create" } | { mode: "edit"; role: Role };

export function RolesPanel({ organization }: { organization: Organization }) {
  const roles = useRoles(organization.id);
  const catalog = usePermissions();
  const actions = useOrganizationActions(organization.id);
  const [editing, setEditing] = useState<Editing | null>(null);
  const [deleting, setDeleting] = useState<Role | null>(null);
  const save = editing?.mode === "edit" ? actions.updateRole : actions.createRole;

  const submit = (values: RoleValues) => {
    const onSuccess = () => setEditing(null);
    if (editing?.mode !== "edit") {
      actions.createRole.mutate(
        { name: values.name, description: values.description || null, permissions: values.permissions },
        { onSuccess },
      );
      return;
    }
    const { role } = editing;
    // Built-in roles keep their name and description.
    const input = role.role_key
      ? { permissions: values.permissions }
      : { name: values.name, description: values.description || null, permissions: values.permissions };
    actions.updateRole.mutate({ roleId: role.id, input }, { onSuccess });
  };

  if (roles.isPending || catalog.isPending) return <Spinner aria-label="Đang tải vai trò" />;
  if (roles.isError || catalog.isError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{organizationErrorMessage(roles.error ?? catalog.error)}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex justify-end">
        <Button onClick={() => setEditing({ mode: "create" })} size="sm">
          <PlusIcon />
          Tạo vai trò
        </Button>
      </div>
      {actions.deleteRole.isError && (
        <Alert variant="destructive">
          <AlertDescription>{organizationErrorMessage(actions.deleteRole.error)}</AlertDescription>
        </Alert>
      )}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Vai trò</TableHead>
            <TableHead>Quyền</TableHead>
            <TableHead>Thành viên</TableHead>
            <TableHead className="w-24" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {roles.data.data.map((role) => (
            <TableRow key={role.id}>
              <TableCell>
                <div className="font-medium">{roleLabel(role)}</div>
                {role.description && (
                  <div className="text-muted-foreground text-xs">{role.description}</div>
                )}
              </TableCell>
              <TableCell>{role.locked ? "Tất cả" : role.permissions.length}</TableCell>
              <TableCell>{role.member_count}</TableCell>
              <TableCell>
                <div className="flex justify-end gap-1">
                  {role.locked ? (
                    <LockIcon
                      aria-label="Vai trò chủ sở hữu luôn có mọi quyền"
                      className="size-4 text-muted-foreground"
                    />
                  ) : (
                    <Button
                      aria-label={`Sửa vai trò ${roleLabel(role)}`}
                      onClick={() => setEditing({ mode: "edit", role })}
                      size="icon"
                      variant="ghost"
                    >
                      <PencilIcon />
                    </Button>
                  )}
                  {!role.role_key && (
                    <Button
                      aria-label={`Xoá vai trò ${roleLabel(role)}`}
                      onClick={() => setDeleting(role)}
                      size="icon"
                      variant="ghost"
                    >
                      <Trash2Icon />
                    </Button>
                  )}
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {editing && (
        <RoleDialog
          catalog={catalog.data.data}
          error={save.isError ? organizationErrorMessage(save.error) : null}
          grantable={organization.is_owner ? null : new Set(organization.permissions)}
          isPending={save.isPending}
          onClose={() => {
            save.reset();
            setEditing(null);
          }}
          onSubmit={submit}
          role={editing.mode === "edit" ? editing.role : undefined}
        />
      )}
      {deleting && (
        <ConfirmDialog
          description={`Các thành viên đang có vai trò ${deleting.name} sẽ mất các quyền của vai trò này.`}
          onClose={() => setDeleting(null)}
          onConfirm={() => {
            actions.deleteRole.mutate(deleting.id);
            setDeleting(null);
          }}
          title="Xoá vai trò?"
        />
      )}
    </div>
  );
}
