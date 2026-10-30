import type { Permission } from "../types/organization.types";

/** Admin screens the member may open, by the permissions the API reports. */
export const MANAGE = {
  organization: "organization.manage",
  members: "member.manage",
  roles: "role.manage",
} as const;

const GROUP_LABELS: Record<string, string> = {
  organization: "Tổ chức",
  member: "Thành viên",
  role: "Vai trò",
  conversation: "Chat",
  tool: "Tool",
};

export type PermissionGroup = { resource: string; label: string; permissions: Permission[] };

/** The catalog grouped by resource, in catalog order, for the role form. */
export function groupPermissions(catalog: readonly Permission[]): PermissionGroup[] {
  const groups = new Map<string, PermissionGroup>();
  for (const permission of catalog) {
    const group = groups.get(permission.resource) ?? {
      resource: permission.resource,
      label: GROUP_LABELS[permission.resource] ?? permission.resource,
      permissions: [],
    };
    group.permissions.push(permission);
    groups.set(permission.resource, group);
  }
  return [...groups.values()];
}

/** Roles shown in Vietnamese; custom roles keep their own names. */
const ROLE_LABELS: Record<string, string> = {
  owner: "Chủ sở hữu",
  admin: "Quản trị",
  member: "Thành viên",
};

export function roleLabel(role: { name: string; role_key?: string | null }): string {
  return (role.role_key && ROLE_LABELS[role.role_key]) || role.name;
}
