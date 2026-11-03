import { describe, expect, it } from "vitest";
import { turnTime, workDuration } from "./turn-time";

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

describe("workDuration", () => {
  const start = "2026-11-02T08:00:00Z";
  const after = (seconds: number) => new Date(Date.parse(start) + seconds * 1000).toISOString();

  it("reads in seconds, then minutes, then hours", () => {
    expect(workDuration(start, after(0.2))).toBe("1 giây");
    expect(workDuration(start, after(7))).toBe("7 giây");
    expect(workDuration(start, after(125))).toBe("2 phút 5 giây");
    expect(workDuration(start, after(180))).toBe("3 phút");
    expect(workDuration(start, after(3780))).toBe("1 giờ 3 phút");
    expect(workDuration(start, undefined)).toBeNull();
  });
});
