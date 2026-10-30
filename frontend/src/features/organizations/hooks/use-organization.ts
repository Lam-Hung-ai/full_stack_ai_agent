"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { workspaceKeys } from "@/features/workspaces";
import {
  createInvitation,
  createOrganization,
  createRole,
  deleteRole,
  getInvitations,
  getMembers,
  getOrganization,
  getPermissions,
  getRoles,
  leaveOrganization,
  removeMember,
  renameOrganization,
  revokeInvitation,
  updateMemberRoles,
  updateRole,
} from "../api/organizations-api";
import type { RoleCreateInput, RoleUpdateInput } from "../types/organization.types";

export const organizationKeys = {
  all: (organizationId: string) => ["organizations", organizationId] as const,
  detail: (organizationId: string) => [...organizationKeys.all(organizationId), "detail"] as const,
  members: (organizationId: string) =>
    [...organizationKeys.all(organizationId), "members"] as const,
  invitations: (organizationId: string) =>
    [...organizationKeys.all(organizationId), "invitations"] as const,
  roles: (organizationId: string) => [...organizationKeys.all(organizationId), "roles"] as const,
};

/** The permission catalog is the same for every organization. */
export const permissionKeys = { all: ["permissions"] as const };

export function useOrganization(organizationId: string) {
  return useQuery({
    queryKey: organizationKeys.detail(organizationId),
    queryFn: ({ signal }) => getOrganization(organizationId, signal),
  });
}

export function useMembers(organizationId: string, enabled = true) {
  return useQuery({
    queryKey: organizationKeys.members(organizationId),
    queryFn: ({ signal }) => getMembers(organizationId, signal),
    enabled,
  });
}

export function useInvitations(organizationId: string, enabled = true) {
  return useQuery({
    queryKey: organizationKeys.invitations(organizationId),
    queryFn: ({ signal }) => getInvitations(organizationId, signal),
    enabled,
  });
}

export function useRoles(organizationId: string, enabled = true) {
  return useQuery({
    queryKey: organizationKeys.roles(organizationId),
    queryFn: ({ signal }) => getRoles(organizationId, signal),
    enabled,
  });
}

export function usePermissions(enabled = true) {
  return useQuery({
    queryKey: permissionKeys.all,
    queryFn: ({ signal }) => getPermissions(signal),
    // Changes only with a deployment.
    staleTime: Infinity,
    enabled,
  });
}

export function useCreateOrganization() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => createOrganization(name),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: workspaceKeys.all, exact: true }),
  });
}

/** Mutations of one organization; each refreshes only what it changed. */
export function useOrganizationActions(organizationId: string) {
  const queryClient = useQueryClient();
  const refresh = (...keys: (readonly unknown[])[]) =>
    Promise.all(keys.map((queryKey) => queryClient.invalidateQueries({ queryKey })));
  const keys = organizationKeys;

  return {
    rename: useMutation({
      mutationFn: (name: string) => renameOrganization(organizationId, name),
      onSuccess: () =>
        refresh(keys.detail(organizationId), workspaceKeys.all),
    }),
    leave: useMutation({
      mutationFn: () => leaveOrganization(organizationId),
      onSuccess: () => {
        queryClient.removeQueries({ queryKey: keys.all(organizationId) });
        return refresh(workspaceKeys.all);
      },
    }),
    updateMemberRoles: useMutation({
      mutationFn: ({ memberId, roleIds }: { memberId: string; roleIds: string[] }) =>
        updateMemberRoles(organizationId, memberId, roleIds),
      // My own roles may have changed, and with them what the screen offers.
      onSuccess: () =>
        refresh(keys.members(organizationId), keys.roles(organizationId), keys.detail(organizationId)),
    }),
    removeMember: useMutation({
      mutationFn: (memberId: string) => removeMember(organizationId, memberId),
      onSuccess: () => refresh(keys.members(organizationId), keys.roles(organizationId)),
    }),
    invite: useMutation({
      mutationFn: (email: string) => createInvitation(organizationId, email),
      onSuccess: () => refresh(keys.invitations(organizationId)),
    }),
    revokeInvitation: useMutation({
      mutationFn: (invitationId: string) => revokeInvitation(organizationId, invitationId),
      onSuccess: () => refresh(keys.invitations(organizationId)),
    }),
    createRole: useMutation({
      mutationFn: (input: RoleCreateInput) => createRole(organizationId, input),
      onSuccess: () => refresh(keys.roles(organizationId)),
    }),
    updateRole: useMutation({
      mutationFn: ({ roleId, input }: { roleId: string; input: RoleUpdateInput }) =>
        updateRole(organizationId, roleId, input),
      onSuccess: () => refresh(keys.roles(organizationId), keys.detail(organizationId)),
    }),
    deleteRole: useMutation({
      mutationFn: (roleId: string) => deleteRole(organizationId, roleId),
      onSuccess: () =>
        refresh(keys.roles(organizationId), keys.members(organizationId), keys.detail(organizationId)),
    }),
  };
}
