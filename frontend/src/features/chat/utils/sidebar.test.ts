import { describe, expect, it } from "vitest";
import { dayLabel, groupByDay } from "./sidebar";

const now = new Date(2026, 10, 2, 9, 0);

describe("dayLabel", () => {
  it("counts calendar days, not 24-hour spans", () => {
    expect(dayLabel(new Date(2026, 10, 2, 0, 5), now)).toBe("Hôm nay");
    expect(dayLabel(new Date(2026, 10, 1, 23, 59), now)).toBe("Hôm qua");
    expect(dayLabel(new Date(2026, 9, 28), now)).toBe("7 ngày qua");
    expect(dayLabel(new Date(2026, 9, 10), now)).toBe("30 ngày qua");
    expect(dayLabel(new Date(2026, 5, 15), now)).toBe("Tháng 6/2026");
  });
});

describe("groupByDay", () => {
  it("keeps the order and joins neighbours with the same label", () => {
    const items = [
      { id: "a", at: new Date(2026, 10, 2, 8).toISOString() },
      { id: "b", at: new Date(2026, 10, 2, 1).toISOString() },
      { id: "c", at: new Date(2026, 10, 1, 12).toISOString() },
      { id: "d", at: new Date(2026, 3, 1).toISOString() },
    ];
    const groups = groupByDay(items, (item) => item.at, now);
    expect(groups.map((group) => [group.label, group.items.map((item) => item.id)])).toEqual([
      ["Hôm nay", ["a", "b"]],
      ["Hôm qua", ["c"]],
      ["Tháng 4/2026", ["d"]],
    ]);
  });
});
