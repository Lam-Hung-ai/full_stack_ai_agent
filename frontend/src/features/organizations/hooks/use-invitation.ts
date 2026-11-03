"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { workspaceKeys } from "@/features/workspaces";
import {
  acceptInvitation,
  previewInvitation,
  registerWithInvitation,
} from "../api/organizations-api";

/** What an invitation link offers; read once, the page acts on it. */
export function useInvitationPreview(token: string) {
  return useQuery({
    queryKey: ["invitations", "preview", token],
    queryFn: () => previewInvitation(token),
    enabled: !!token,
    staleTime: Infinity,
  });
}

export function useAcceptInvitation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (token: string) => acceptInvitation(token),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: workspaceKeys.all, exact: true }),
  });
}

export function useRegisterWithInvitation() {
  return useMutation({ mutationFn: registerWithInvitation });
}
