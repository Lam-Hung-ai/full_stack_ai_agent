import { apiClient } from "@/lib/api";
import type {
  LoginInput,
  PasswordResetInput,
  RegisterInput,
  SessionResponse,
  TokenResponse,
  User,
} from "../types/auth.types";

export function login(input: LoginInput) {
  return apiClient<TokenResponse>("/api/v1/auth/login", { method: "POST", body: input });
}

export function register(input: RegisterInput) {
  return apiClient<User>("/api/v1/auth/register", { method: "POST", body: input });
}

/** Rotate the refresh cookie and load the user in one round trip. */
export function startSession() {
  return apiClient<SessionResponse>("/api/v1/auth/session", { method: "POST" });
}

export function logout() {
  return apiClient<void>("/api/v1/auth/logout", { method: "POST" });
}

/** 202 whether or not the email has an account. */
export function requestPasswordReset(email: string) {
  return apiClient<void>("/api/v1/auth/password-reset/request", {
    method: "POST",
    body: { email },
  });
}

export function confirmPasswordReset(input: PasswordResetInput) {
  return apiClient<void>("/api/v1/auth/password-reset/confirm", { method: "POST", body: input });
}

/** 202 whether or not the email has an unverified account. */
export function requestEmailVerification(email: string) {
  return apiClient<void>("/api/v1/auth/email-verification/request", {
    method: "POST",
    body: { email },
  });
}

export function confirmEmail(token: string) {
  return apiClient<void>("/api/v1/auth/email-verification/confirm", {
    method: "POST",
    body: { token },
  });
}
