import { describe, expect, it } from "vitest";
import { ApiError } from "@/lib/api";
import { retryNetworkFailure } from "./providers";

describe("retryNetworkFailure", () => {
  it("retries a failure that never reached the server, a bounded number of times", () => {
    const offline = new ApiError(0, "network_error");
    expect(retryNetworkFailure(0, offline)).toBe(true);
    expect(retryNetworkFailure(2, offline)).toBe(false);
  });

  it("does not retry an answer from FastAPI", () => {
    expect(retryNetworkFailure(0, new ApiError(404, "not_found"))).toBe(false);
  });
});
