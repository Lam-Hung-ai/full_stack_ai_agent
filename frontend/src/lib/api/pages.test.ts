import { describe, expect, it, vi } from "vitest";
import { allPages } from "./pages";

describe("allPages", () => {
  it("follows has_next_page and merges every page", async () => {
    const fetchPage = vi.fn(async (page: number) => ({
      data: [page * 10, page * 10 + 1],
      pagination: { page, has_next_page: page < 3 },
      extra: "kept",
    }));
    const result = await allPages(fetchPage);
    expect(result.data).toEqual([10, 11, 20, 21, 30, 31]);
    expect(result.extra).toBe("kept");
    expect(fetchPage).toHaveBeenCalledTimes(3);
  });
});
