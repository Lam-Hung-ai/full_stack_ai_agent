export type DayGroup<T> = { label: string; items: T[] };

const DAY_MS = 86_400_000;

function startOfDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

/** The group of a date, by local calendar days before `now`. */
export function dayLabel(date: Date, now: Date): string {
  // Rounded: a day across a daylight-saving change is not 24 hours.
  const days = Math.round((startOfDay(now) - startOfDay(date)) / DAY_MS);
  if (days <= 0) return "Hôm nay";
  if (days === 1) return "Hôm qua";
  if (days < 7) return "7 ngày qua";
  if (days < 30) return "30 ngày qua";
  return `Tháng ${date.getMonth() + 1}/${date.getFullYear()}`;
}

/** Runs of items with the same day label, keeping the given (newest first) order. */
export function groupByDay<T>(
  items: readonly T[],
  dateOf: (item: T) => string,
  now = new Date(),
): DayGroup<T>[] {
  const groups: DayGroup<T>[] = [];
  for (const item of items) {
    const label = dayLabel(new Date(dateOf(item)), now);
    const last = groups.at(-1);
    if (last?.label === label) last.items.push(item);
    else groups.push({ label, items: [item] });
  }
  return groups;
}
