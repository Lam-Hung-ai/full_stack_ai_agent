/** Shared FastAPI transport: JSON in and out, one error type for every failure. */
import { env } from "@/config/env";
import { ApiError, toApiError } from "./api-error";

type QueryValue = string | number | boolean | null | undefined;

export type ApiClientOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  query?: Record<string, QueryValue>;
  headers?: HeadersInit;
  signal?: AbortSignal;
};

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
    response = await fetch(apiUrl(path, options.query), {
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
  if (!response.ok) throw await toApiError(response);
  return response;
}

/** JSON request; resolves `undefined` for 204 No Content. Never retries. */
export async function apiClient<T>(path: string, options: ApiClientOptions = {}): Promise<T> {
  const response = await send(path, options);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
