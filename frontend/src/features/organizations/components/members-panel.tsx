"use client";

import { useState } from "react";
import { ShieldIcon, UserMinusIcon } from "lucide-react";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
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
import { useMembers, useOrganizationActions } from "../hooks/use-organization";
import type { Member } from "../types/organization.types";
import { organizationErrorMessage } from "../utils/error-message";
import { roleLabel } from "../utils/permissions";
import { MemberRolesDialog } from "./member-roles-dialog";

export function MembersPanel({
  organizationId,
  currentUserId,
  canAssignRoles,
}: {
  organizationId: string;
  currentUserId: string;
  canAssignRoles: boolean;
}) {
  const members = useMembers(organizationId);
  const actions = useOrganizationActions(organizationId);
  const [editing, setEditing] = useState<Member | null>(null);
  const [removing, setRemoving] = useState<Member | null>(null);
  const error = actions.removeMember.error;

  if (members.isPending) return <Spinner aria-label="Đang tải thành viên" />;
  if (members.isError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{organizationErrorMessage(members.error)}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{organizationErrorMessage(error)}</AlertDescription>
        </Alert>
      )}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Thành viên</TableHead>
            <TableHead>Vai trò</TableHead>
            <TableHead className="w-24" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {members.data.data.map((member) => (
            <TableRow key={member.id}>
              <TableCell>
                <div className="font-medium">
                  {member.name}
                  {member.user_id === currentUserId && (
                    <span className="text-muted-foreground"> (bạn)</span>
                  )}
                </div>
                <div className="text-muted-foreground text-xs">{member.email}</div>
              </TableCell>
              <TableCell>
                <div className="flex flex-wrap gap-1">
                  {member.roles.map((role) => (
                    <Badge key={role.id} variant="secondary">
                      {roleLabel(role)}
                    </Badge>
                  ))}
                </div>
              </TableCell>
              <TableCell>
                <div className="flex justify-end gap-1">
                  {canAssignRoles && (
                    <Button
                      aria-label={`Đổi vai trò của ${member.name}`}
                      onClick={() => setEditing(member)}
                      size="icon"
                      variant="ghost"
                    >
                      <ShieldIcon />
                    </Button>
                  )}
                  {member.user_id !== currentUserId && (
                    <Button
                      aria-label={`Xoá ${member.name} khỏi tổ chức`}
                      onClick={() => setRemoving(member)}
                      size="icon"
                      variant="ghost"
                    >
                      <UserMinusIcon />
                    </Button>
                  )}
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {editing && (
        <MemberRolesDialog
          member={editing}
          onClose={() => setEditing(null)}
          organizationId={organizationId}
        />
      )}
      {removing && (
        <ConfirmDialog
          confirmLabel="Xoá khỏi tổ chức"
          description={`${removing.name} mất quyền vào tổ chức và các chat của họ ở đây; lượt trả lời đang chạy của họ bị dừng.`}
          onClose={() => setRemoving(null)}
          onConfirm={() => {
            actions.removeMember.mutate(removing.id);
            setRemoving(null);
          }}
          title="Xoá thành viên?"
        />
      )}
    </div>
  );
}
