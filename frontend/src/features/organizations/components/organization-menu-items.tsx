"use client";

import { BuildingIcon, PlusIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { useCurrentWorkspace } from "@/features/workspaces";

/** Workspace menu entries: manage the current organization, create one. */
export function OrganizationMenuItems() {
  const router = useRouter();
  const current = useCurrentWorkspace();
  return (
    <>
      {current?.organization_id && (
        <DropdownMenuItem
          onSelect={() => router.push(`/organizations/${current.organization_id}`)}
        >
          <BuildingIcon />
          Quản lý tổ chức
        </DropdownMenuItem>
      )}
      <DropdownMenuItem onSelect={() => router.push("/organizations/new")}>
        <PlusIcon />
        Tạo tổ chức
      </DropdownMenuItem>
    </>
  );
}
