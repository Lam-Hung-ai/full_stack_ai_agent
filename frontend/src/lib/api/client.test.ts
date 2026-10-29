import { afterEach, describe, expect, it, vi } from "vitest";
import {
  clearAccessToken,
  getAccessToken,
  onSessionExpired,
  setAccessToken,
} from "@/lib/auth/session";
import { ApiError } from "./api-error";
import { apiClient, apiUrl } from "./client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiUrl", () => {
  it("drops empty query values", () => {
    expect(apiUrl("/api/v1/x", { a: 1, b: undefined, c: null, d: "y" })).toBe(
      "/api/v1/x?a=1&d=y",
    );
  });
});

describe("apiClient", () => {
  it("sends JSON with credentials and parses the response", async () => {
    const fetchMock = vi.fn(async () => Response.json({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiClient("/api/v1/x", { method: "POST", body: { a: 1 } })).resolves.toEqual({
      ok: true,
    });
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(init.credentials).toBe("include");
    expect(new Headers(init.headers).get("Content-Type")).toBe("application/json");
    expect(init.body).toBe('{"a":1}');
  });

  it("resolves undefined for 204", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(null, { status: 204 })));
    await expect(apiClient("/api/v1/x", { method: "DELETE" })).resolves.toBeUndefined();
  });

  it("maps the FastAPI error contract", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        Response.json(
          { error: { code: "demo_conflict", message: "Xung đột", request_id: "r1" } },
          { status: 409 },
        ),
      ),
    );
    const error = await apiClient("/api/v1/x").catch((caught: unknown) => caught);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 409,
      code: "demo_conflict",
      message: "Xung đột",
      requestId: "r1",
    });
  });

  it("tolerates a non-JSON error body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("<html>", { status: 502, headers: { "x-request-id": "r2" } })),
    );
    await expect(apiClient("/api/v1/x")).rejects.toMatchObject({
      status: 502,
      code: "http_error",
      requestId: "r2",
    });
  });

  it("reports a network failure as status 0", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => Promise.reject(new TypeError("Failed to fetch"))));
    await expect(apiClient("/api/v1/x")).rejects.toMatchObject({
      status: 0,
      code: "network_error",
    });
  });
});

describe("apiClient with a session", () => {
  afterEach(() => {
    clearAccessToken();
  });

  it("attaches the access token", async () => {
    setAccessToken("t1");
    const fetchMock = vi.fn(async () => Response.json({}));
    vi.stubGlobal("fetch", fetchMock);
    await apiClient("/api/v1/users/me");
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer t1");
  });

  it("refreshes once for concurrent 401s and replays each request", async () => {
    setAccessToken("old");
    let refreshes = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init: RequestInit) => {
        if (url.endsWith("/api/v1/auth/refresh")) {
          refreshes += 1;
          return Response.json({ access_token: "new" });
        }
        const auth = new Headers(init.headers).get("Authorization");
        return auth === "Bearer new"
          ? Response.json({ ok: true })
          : Response.json({ error: { code: "invalid_access_token" } }, { status: 401 });
      }),
    );

    const results = await Promise.all([apiClient("/api/v1/a"), apiClient("/api/v1/b")]);
    expect(results).toEqual([{ ok: true }, { ok: true }]);
    expect(refreshes).toBe(1);
    expect(getAccessToken()).toBe("new");
  });

  it("reports an expired session when the refresh fails", async () => {
    setAccessToken("old");
    const expired = vi.fn();
    const unsubscribe = onSessionExpired(expired);
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => Response.json({ error: { code: "x" } }, { status: 401 })),
    );
    await expect(apiClient("/api/v1/a")).rejects.toMatchObject({ status: 401 });
    expect(expired).toHaveBeenCalledOnce();
    expect(getAccessToken()).toBeNull();
    unsubscribe();
  });

  it("does not refresh for auth endpoints or anonymous requests", async () => {
    const fetchMock = vi.fn(async () =>
      Response.json({ error: { code: "invalid_credentials" } }, { status: 401 }),
    );
    vi.stubGlobal("fetch", fetchMock);
    await expect(apiClient("/api/v1/auth/login", { method: "POST" })).rejects.toMatchObject({
      code: "invalid_credentials",
    });
    expect(fetchMock).toHaveBeenCalledOnce();
  });
});
