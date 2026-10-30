import { apiClient } from "@/lib/api";
import type {
  Invitation,
  InvitationPreview,
  JoinedOrganization,
  Member,
  MemberList,
  Organization,
  Permission,
  Role,
  RoleCreateInput,
  RoleUpdateInput,
} from "../types/organization.types";

const base = (organizationId: string) => `/api/v1/organizations/${organizationId}`;

export function createOrganization(name: string) {
  return apiClient<Organization>("/api/v1/organizations", { method: "POST", body: { name } });
}

export function getOrganization(organizationId: string, signal?: AbortSignal) {
  return apiClient<Organization>(base(organizationId), { signal });
}

export function renameOrganization(organizationId: string, name: string) {
  return apiClient<Organization>(base(organizationId), { method: "PATCH", body: { name } });
}

export function leaveOrganization(organizationId: string) {
  return apiClient<void>(`${base(organizationId)}/leave`, { method: "POST" });
}

export function getMembers(organizationId: string, signal?: AbortSignal) {
  // One page holds every member of the organizations this screen serves.
  return apiClient<MemberList>(`${base(organizationId)}/members`, {
    query: { page_size: 100 },
    signal,
  });
}

export function updateMemberRoles(organizationId: string, memberId: string, roleIds: string[]) {
  return apiClient<Member>(`${base(organizationId)}/members/${memberId}`, {
    method: "PATCH",
    body: { role_ids: roleIds },
  });
}

export function removeMember(organizationId: string, memberId: string) {
  return apiClient<void>(`${base(organizationId)}/members/${memberId}`, { method: "DELETE" });
}

export function getInvitations(organizationId: string, signal?: AbortSignal) {
  return apiClient<{ data: Invitation[] }>(`${base(organizationId)}/invitations`, { signal });
}

export function createInvitation(organizationId: string, email: string) {
  return apiClient<Invitation>(`${base(organizationId)}/invitations`, {
    method: "POST",
    body: { email },
  });
}

export function revokeInvitation(organizationId: string, invitationId: string) {
  return apiClient<void>(`${base(organizationId)}/invitations/${invitationId}`, {
    method: "DELETE",
  });
}

export function getRoles(organizationId: string, signal?: AbortSignal) {
  return apiClient<{ data: Role[] }>(`${base(organizationId)}/roles`, { signal });
}

export function createRole(organizationId: string, input: RoleCreateInput) {
  return apiClient<Role>(`${base(organizationId)}/roles`, { method: "POST", body: input });
}

export function updateRole(organizationId: string, roleId: string, input: RoleUpdateInput) {
  return apiClient<Role>(`${base(organizationId)}/roles/${roleId}`, {
    method: "PATCH",
    body: input,
  });
}

export function deleteRole(organizationId: string, roleId: string) {
  return apiClient<void>(`${base(organizationId)}/roles/${roleId}`, { method: "DELETE" });
}

export function getPermissions(signal?: AbortSignal) {
  return apiClient<{ data: Permission[] }>("/api/v1/permissions", { signal });
}

// Invitation links: the token goes in the body, never in an API URL.

export function previewInvitation(token: string) {
  return apiClient<InvitationPreview>("/api/v1/invitations/preview", {
    method: "POST",
    body: { token },
  });
}

export function acceptInvitation(token: string) {
  return apiClient<JoinedOrganization>("/api/v1/invitations/accept", {
    method: "POST",
    body: { token },
  });
}

export function registerWithInvitation(input: { token: string; name: string; password: string }) {
  return apiClient<JoinedOrganization>("/api/v1/invitations/register", {
    method: "POST",
    body: input,
  });
}
