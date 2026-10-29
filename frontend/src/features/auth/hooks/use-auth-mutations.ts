"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { clearAccessToken, setAccessToken } from "@/lib/auth/session";
import { login, logout, register } from "../api/auth-api";
import type { LoginValues, RegisterValues } from "../schemas/auth.schema";
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
