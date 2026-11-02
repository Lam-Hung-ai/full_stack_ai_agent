const MINUTE_MS = 60_000;

/** A turn's time under it: "Vừa xong", "5 phút trước", "14:05", "6 thg 10", "6/10/2025". */
export function turnTime(iso: string | undefined, now = new Date()): string {
  if (!iso) return "Vừa xong";
  const date = new Date(iso);
  const minutes = Math.floor((now.getTime() - date.getTime()) / MINUTE_MS);
  if (minutes < 1) return "Vừa xong";
  if (minutes < 60) return `${minutes} phút trước`;
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
  }
  if (date.getFullYear() === now.getFullYear()) {
    return `${date.getDate()} thg ${date.getMonth() + 1}`;
  }
  return `${date.getDate()}/${date.getMonth() + 1}/${date.getFullYear()}`;
}

/** The full date and time, for a tooltip. */
export function turnTimeTitle(iso: string | undefined): string | undefined {
  return iso ? new Date(iso).toLocaleString("vi-VN") : undefined;
}
