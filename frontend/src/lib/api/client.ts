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

/** `expired`: the server refused the refresh cookie. `unavailable`: no answer
 * (network, proxy 5xx during a deploy); the session may still be fine. */
type RefreshResult = "refreshed" | "expired" | "unavailable";

let refreshing: Promise<RefreshResult> | null = null;

/**
 * Exchange the refresh cookie for a new access token. Concurrent 401s share
 * one call: two refreshes with the same cookie would look like token reuse to
 * the backend and revoke the whole session.
 */
export function refreshAccessToken(): Promise<RefreshResult> {
  refreshing ??= (async (): Promise<RefreshResult> => {
    try {
      const response = await fetch(apiUrl(`${AUTH_PREFIX}refresh`), {
        method: "POST",
        credentials: "include",
      });
      if (response.status === 401 || response.status === 403) return "expired";
      if (!response.ok) return "unavailable";
      const body = (await response.json()) as { access_token: string };
      setAccessToken(body.access_token);
      return "refreshed";
    } catch {
      return "unavailable";
    } finally {
      refreshing = null;
    }
  })();
  return refreshing;
}

function withAuthorization(init: RequestInit): RequestInit {
  const headers = new Headers(init.headers);
  const token = getAccessToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return { ...init, headers, credentials: "include" };
}

/**
 * `fetch` with the session's access token. A 401 refreshes once and replays
 * the request: the backend rejected it before doing anything, so this is not
 * a mutation retry. Returns the response whatever its status, which lets
 * stream readers (the AG-UI agent) handle errors their own way.
 */
export async function authorizedFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const hadToken = getAccessToken() !== null;
  let response = await fetch(url, withAuthorization(init));
  if (response.status === 401 && hadToken && !url.includes(AUTH_PREFIX)) {
    const refreshed = await refreshAccessToken();
    if (refreshed === "refreshed") {
      response = await fetch(url, withAuthorization(init));
    } else if (refreshed === "expired") {
      notifySessionExpired();
    } else {
      // Fails like a lost connection: reads retry, the user stays signed in.
      throw new TypeError("Could not refresh the session");
    }
  }
  return response;
}

/** Send a request and return the raw response once it is known to be 2xx. */
export async function send(path: string, options: ApiClientOptions = {}): Promise<Response> {
  const headers = new Headers(options.headers);
  let body: BodyInit | undefined;
  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.body);
  }
  let response: Response;
  try {
    response = await authorizedFetch(apiUrl(path, options.query), {
      method: options.method ?? "GET",
      headers,
      body,
      signal: options.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(0, "network_error");
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
