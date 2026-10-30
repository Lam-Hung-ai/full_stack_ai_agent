// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from "vitest";

import { StorageUploadError, uploadPresignedFile } from "./upload";

describe("uploadPresignedFile", () => {
  afterEach(() => vi.restoreAllMocks());

  it("uploads only the signed headers and omits application credentials", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const file = new File(["avatar"], "avatar.png", { type: "image/png" });

    await uploadPresignedFile(file, {
      url: "http://localhost:9000/hr-ai/private/temp/avatar?signed=1",
      method: "PUT",
      headers: { "Content-Type": "image/png" },
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:9000/hr-ai/private/temp/avatar?signed=1",
      expect.objectContaining({
        body: file,
        credentials: "omit",
        headers: { "Content-Type": "image/png" },
        method: "PUT",
      }),
    );
  });

  it("rejects a failed object-storage response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 403 })),
    );

    await expect(
      uploadPresignedFile(
        new File(["avatar"], "avatar.png", { type: "image/png" }),
        {
          url: "http://localhost:9000/signed",
          method: "PUT",
          headers: { "Content-Type": "image/png" },
        },
      ),
    ).rejects.toEqual(new StorageUploadError("storage_upload_rejected", 403));
  });

  it("reports an unreachable object-storage endpoint", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(
      uploadPresignedFile(
        new File(["avatar"], "avatar.png", { type: "image/png" }),
        {
          url: "http://localhost:9000/signed",
          method: "PUT",
          headers: { "Content-Type": "image/png" },
        },
      ),
    ).rejects.toEqual(new StorageUploadError("storage_upload_unreachable"));
  });
});
