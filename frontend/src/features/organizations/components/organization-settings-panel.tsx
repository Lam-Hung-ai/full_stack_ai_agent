"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { NameDialog } from "@/components/shared/name-dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useOrganizationActions } from "../hooks/use-organization";
import type { Organization } from "../types/organization.types";
import { organizationErrorMessage } from "../utils/error-message";
import { MANAGE } from "../utils/permissions";

export function OrganizationSettingsPanel({ organization }: { organization: Organization }) {
  const router = useRouter();
  const { rename, leave } = useOrganizationActions(organization.id);
  const [dialog, setDialog] = useState<"rename" | "leave" | null>(null);
  const canRename = organization.permissions.includes(MANAGE.organization);

  return (
    <div className="flex max-w-xl flex-col gap-6">
      {canRename && (
        <section className="flex items-center justify-between gap-4">
          <div>
            <h3 className="font-medium">Tên tổ chức</h3>
            <p className="text-muted-foreground text-sm">{organization.name}</p>
          </div>
          <Button onClick={() => setDialog("rename")} variant="outline">
            Đổi tên
          </Button>
        </section>
      )}
      <section className="flex items-center justify-between gap-4">
        <div>
          <h3 className="font-medium">Rời tổ chức</h3>
          <p className="text-muted-foreground text-sm">
            Bạn mất quyền vào workspace này và các chat của bạn ở đây.
          </p>
        </div>
        <Button onClick={() => setDialog("leave")} variant="destructive">
          Rời tổ chức
        </Button>
      </section>
      {leave.isError && (
        <Alert variant="destructive">
          <AlertDescription>{organizationErrorMessage(leave.error)}</AlertDescription>
        </Alert>
      )}
      {dialog === "rename" && (
        <NameDialog
          defaultName={organization.name}
          error={rename.isError ? organizationErrorMessage(rename.error) : null}
          isPending={rename.isPending}
          label="Tên tổ chức"
          onClose={() => {
            rename.reset();
            setDialog(null);
          }}
          onSubmit={(name) => rename.mutate(name, { onSuccess: () => setDialog(null) })}
          title="Đổi tên tổ chức"
        />
      )}
      {dialog === "leave" && (
        <ConfirmDialog
          confirmLabel="Rời tổ chức"
          description={`Bạn sẽ không còn thấy ${organization.name} và các chat của bạn trong đó.`}
          onClose={() => setDialog(null)}
          onConfirm={() => {
            setDialog(null);
            leave.mutate(undefined, { onSuccess: () => router.replace("/") });
          }}
          title="Rời tổ chức?"
        />
      )}
    </div>
  );
}
