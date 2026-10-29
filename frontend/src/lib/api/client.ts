/** Shared FastAPI transport: auth and refresh, JSON, one error type for every failure. */
import { env } from "@/config/env";
import {
  getAccessToken,
  notifySessionExpired,
  setAccessToken,
} from "@/lib/auth/session";
import { ApiError, toApiError } from "./api-error";

type QueryValue = string | number | boolean | null | undefined;

export type ApiClientOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  query?: Record<string, QueryValue>;
  headers?: HeadersInit;
  signal?: AbortSignal;
};

const AUTH_PREFIX = "/api/v1/auth/";

export function apiUrl(path: string, query?: Record<string, QueryValue>): string {
  const url = `${env.apiUrl}${path}`;
  if (!query) return url;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null) params.set(key, String(value));
  }
  const search = params.toString();
  return search ? `${url}?${search}` : url;
}

let refreshing: Promise<boolean> | null = null;

/**
 * Exchange the refresh cookie for a new access token. Concurrent 401s share
 * one call: two refreshes with the same cookie would look like token reuse to
 * the backend and revoke the whole session.
 */
export function refreshAccessToken(): Promise<boolean> {
  refreshing ??= (async () => {
    try {
      const response = await fetch(apiUrl(`${AUTH_PREFIX}refresh`), {
        method: "POST",
        credentials: "include",
      });
      if (!response.ok) return false;
      const body = (await response.json()) as { access_token: string };
      setAccessToken(body.access_token);
      return true;
    } catch {
      return false;
    } finally {
      refreshing = null;
    }
  })();
  return refreshing;
}

async function request(path: string, options: ApiClientOptions): Promise<Response> {
  const headers = new Headers(options.headers);
  let body: BodyInit | undefined;
  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.body);
  }
  const token = getAccessToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  try {
    return await fetch(apiUrl(path, options.query), {
      method: options.method ?? "GET",
      headers,
      body,
      signal: options.signal,
      credentials: "include",
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(0, "network_error");
  }
}

/**
 * Send a request and return the raw response once it is known to be 2xx.
 *
 * A 401 with an access token refreshes once and replays the request: the
 * backend rejected it before doing anything, so this is not a mutation retry.
 */
export async function send(path: string, options: ApiClientOptions = {}): Promise<Response> {
  const hadToken = getAccessToken() !== null;
  let response = await request(path, options);
  if (response.status === 401 && hadToken && !path.startsWith(AUTH_PREFIX)) {
    if (await refreshAccessToken()) {
      response = await request(path, options);
    } else {
      notifySessionExpired();
    }
  }
  if (!response.ok) throw await toApiError(response);
  return response;
}

/** JSON request; resolves `undefined` for 204 No Content. Never retries a failure. */
export async function apiClient<T>(path: string, options: ApiClientOptions = {}): Promise<T> {
  const response = await send(path, options);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
