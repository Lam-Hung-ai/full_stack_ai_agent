import type { WorkStep } from "./answer-blocks";
import { CREATE_FILE_TOOL, formatBytes, madeFile } from "./files";

type ToolStep = Extract<WorkStep, { kind: "tool" }>;

const CLOCK_TOOL = "get_current_time";
/** Longest plain-text result shown as is on the step line. */
const SHORT_RESULT = 80;

/** What a run did, in a few words, for its header: "xem giờ, tạo 2 tệp". */
export function workDone(steps: readonly WorkStep[]): string {
  const counts = new Map<string, number>();
  for (const step of steps) {
    if (step.kind === "tool") {
      const name = step.call.function.name;
      counts.set(name, (counts.get(name) ?? 0) + 1);
    }
  }
  if (counts.size === 0) return "suy nghĩ";
  return [...counts]
    .map(([name, count]) => {
      if (name === CLOCK_TOOL) return count > 1 ? `xem giờ ${count} lần` : "xem giờ";
      if (name === CREATE_FILE_TOOL) return `tạo ${count} tệp`;
      return count > 1 ? `${name} ×${count}` : name;
    })
    .join(", ");
}

/**
 * A tool's result in words for its step line ("09:40 3/11/2026",
 * "báo cáo.xlsx · 4.9 KB"), or its error; null when it has none or the
 * result is too long to read in a line (it stays in the technical details).
 */
export function toolResultText(step: ToolStep): { text: string; isError: boolean } | null {
  const result = step.result;
  if (!result) return null;
  if (result.error) return { text: result.error, isError: true };
  const content = typeof result.content === "string" ? result.content.trim() : "";
  const name = step.call.function.name;
  if (name === CLOCK_TOOL) {
    const time = new Date(content);
    if (!Number.isNaN(time.getTime())) {
      return {
        text: time.toLocaleString("vi-VN", {
          hour: "2-digit",
          minute: "2-digit",
          day: "numeric",
          month: "numeric",
          year: "numeric",
        }),
        isError: false,
      };
    }
  }
  const made = madeFile(name, content);
  if (made) return { text: `${made.name} · ${formatBytes(made.sizeBytes)}`, isError: false };
  if (content && content.length <= SHORT_RESULT && !content.includes("\n")) {
    return { text: content, isError: false };
  }
  return null;
}
