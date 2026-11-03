import type { WorkStep } from "./answer-blocks";
import { CREATE_FILE_TOOL, formatBytes, madeFile } from "./files";

type ToolStep = Extract<WorkStep, { kind: "tool" }>;

const CLOCK_TOOL = "get_current_time";
/** Longest plain-text result shown as is on the step line. */
const SHORT_RESULT = 80;

/**
 * What a run did, in a few words, for its header: "xem giờ, tạo 2 tệp".
 * Only files actually made are counted (failed calls show as "bước lỗi");
 * a tool that only failed reads as tried ("thử tạo tệp").
 */
export function workDone(steps: readonly WorkStep[]): string {
  const counts = new Map<string, { done: number; failed: number }>();
  for (const step of steps) {
    if (step.kind !== "tool") continue;
    const count = counts.get(step.call.function.name) ?? { done: 0, failed: 0 };
    if (step.result?.error) count.failed += 1;
    else count.done += 1;
    counts.set(step.call.function.name, count);
  }
  if (counts.size === 0) return "suy nghĩ";
  return [...counts]
    .map(([name, { done, failed }]) => {
      if (name === CREATE_FILE_TOOL) return done > 0 ? `tạo ${done} tệp` : "thử tạo tệp";
      if (done === 0 && failed > 0) return name === CLOCK_TOOL ? "thử xem giờ" : `thử ${name}`;
      if (name === CLOCK_TOOL) return done > 1 ? `xem giờ ${done} lần` : "xem giờ";
      return done > 1 ? `${name} ×${done}` : name;
    })
    .join(", ");
}

/**
 * A failed tool's message. ag-ui-langgraph can only flag LangChain's error
 * status with the fixed text "error"; the tool's own words are the content.
 */
export function toolErrorText(error: string, content: string): string {
  return error === "error" ? content || "Công cụ báo lỗi" : error;
}

/**
 * A tool's result in words for its step line ("09:40 3/11/2026",
 * "báo cáo.xlsx · 4.9 KB"), or its error; null when it has none or the
 * result is too long to read in a line (it stays in the technical details).
 */
export function toolResultText(step: ToolStep): { text: string; isError: boolean } | null {
  const result = step.result;
  if (!result) return null;
  const content = typeof result.content === "string" ? result.content.trim() : "";
  if (result.error) return { text: toolErrorText(result.error, content), isError: true };
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
