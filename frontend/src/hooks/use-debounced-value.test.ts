// @vitest-environment jsdom
import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useDebouncedValue } from "./use-debounced-value";

describe("useDebouncedValue", () => {
  afterEach(() => vi.useRealTimers());

  it("settles on the last value once input stops", () => {
    vi.useFakeTimers();
    const { result, rerender } = renderHook(({ value }) => useDebouncedValue(value, 300), {
      initialProps: { value: "h" },
    });
    rerender({ value: "ha" });
    rerender({ value: "ha n" });
    act(() => vi.advanceTimersByTime(299));
    expect(result.current).toBe("h");
    act(() => vi.advanceTimersByTime(1));
    expect(result.current).toBe("ha n");
  });
});
