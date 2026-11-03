"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { clearAccessToken, setAccessToken } from "@/lib/auth/session";
import {
  confirmEmail,
  confirmPasswordReset,
  login,
  logout,
  register,
  requestEmailVerification,
  requestPasswordReset,
} from "../api/auth-api";
import type { LoginValues, RegisterValues } from "../schemas/auth.schema";
import type { PasswordResetInput, SessionResponse } from "../types/auth.types";
import { sessionKey } from "./use-session";

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (values: LoginValues) => login(values),
    onSuccess: (token) => {
      setAccessToken(token.access_token);
      // The app layout loads profile and workspaces once it mounts. Removing
      // instead of resetting avoids a cancelled-and-repeated session call.
      queryClient.removeQueries({ queryKey: sessionKey });
    },
  });
}

export function useRegister() {
  return useMutation({ mutationFn: (values: RegisterValues) => register(values) });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => logout(),
    onSettled: () => {
      // Drop the token and every cached response, whatever the server said.
      clearAccessToken();
      queryClient.clear();
    },
  });
}

export function useRequestPasswordReset() {
  return useMutation({ mutationFn: (email: string) => requestPasswordReset(email) });
}

export function useResetPassword() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: PasswordResetInput) => confirmPasswordReset(input),
    // The server signed every session out, this one included.
    onSuccess: () => {
      clearAccessToken();
      queryClient.clear();
    },
  });
}

export function useRequestEmailVerification() {
  return useMutation({ mutationFn: (email: string) => requestEmailVerification(email) });
}

export function useConfirmEmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (token: string) => confirmEmail(token),
    onSuccess: () => {
      // The open session, if any, still says unverified.
      queryClient.setQueryData<SessionResponse>(sessionKey, (session) =>
        session ? { ...session, user: { ...session.user, email_verified: true } } : session,
      );
    },
  });
}
