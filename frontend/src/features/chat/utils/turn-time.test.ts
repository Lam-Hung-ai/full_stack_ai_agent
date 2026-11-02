import { describe, expect, it } from "vitest";
import { turnTime } from "./turn-time";

const now = new Date(2026, 10, 2, 15, 30);
const at = (...parts: [number, number, number, number?, number?]) =>
  new Date(...parts).toISOString();

describe("turnTime", () => {
  it("is relative within the hour, a clock time today, a date before", () => {
    expect(turnTime(undefined, now)).toBe("Vừa xong");
    expect(turnTime(at(2026, 10, 2, 15, 29), now)).toBe("1 phút trước");
    expect(turnTime(new Date(now.getTime() - 20_000).toISOString(), now)).toBe("Vừa xong");
    expect(turnTime(at(2026, 10, 2, 9, 5), now)).toBe("09:05");
    expect(turnTime(at(2026, 9, 6, 9, 5), now)).toBe("6 thg 10");
    expect(turnTime(at(2025, 9, 6), now)).toBe("6/10/2025");
  });
});
