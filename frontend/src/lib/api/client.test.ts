import { afterEach, describe, expect, it, vi } from "vitest";
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
