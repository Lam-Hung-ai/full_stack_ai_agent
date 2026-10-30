import type { Message as AGUIMessage } from "@ag-ui/client";
import type { ChatFile } from "../api/files-api";

/** Mirrors the backend policy (`modules/files/policy.py`); it checks again. */
export const ACCEPTED_FILES = ".png,.jpg,.jpeg,.gif,.webp,.pdf,.txt,.log,.md,.markdown,.csv,.json";
export const MAX_FILE_BYTES = 10 * 1024 * 1024;
export const MAX_FILES = 10;

/** Content types by extension, for browsers that leave `File.type` empty. */
const TYPES: Record<string, string> = {
  png: "image/png",
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  gif: "image/gif",
  webp: "image/webp",
  pdf: "application/pdf",
  txt: "text/plain",
  log: "text/plain",
  md: "text/markdown",
  markdown: "text/markdown",
  csv: "text/csv",
  json: "application/json",
};

export function contentTypeOf(file: { name: string; type: string }): string {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  return TYPES[extension] ?? file.type;
}

/** A file attached to a stored question, as its AG-UI media part names it. */
export type AttachedFile = {
  id: string;
  name: string;
  contentType: string;
  sizeBytes: number;
  isImage: boolean;
};

type MediaPart = {
  type: string;
  id?: string;
  source?: { type?: string; value?: string; mimeType?: string };
  metadata?: { filename?: string; sizeBytes?: number };
};

const STORED_FILE = "stored-file:";

function parts(message: AGUIMessage | undefined): MediaPart[] {
  const content = (message as { content?: unknown } | undefined)?.content;
  return Array.isArray(content) ? (content as MediaPart[]) : [];
}

/** The question's text, whether stored as a string or as content parts. */
export function questionText(message: AGUIMessage | undefined): string {
  const content = (message as { content?: unknown } | undefined)?.content;
  if (typeof content === "string") return content;
  return parts(message)
    .flatMap((part) => (part.type === "text" ? [(part as { text?: string }).text ?? ""] : []))
    .join("\n");
}

export function attachedFiles(message: AGUIMessage | undefined): AttachedFile[] {
  return parts(message).flatMap((part) =>
    part.id && part.source?.value?.startsWith(STORED_FILE)
      ? [
          {
            id: part.id,
            name: part.metadata?.filename ?? "tệp",
            contentType: part.source.mimeType ?? "",
            sizeBytes: part.metadata?.sizeBytes ?? 0,
            isImage: part.type === "image",
          },
        ]
      : [],
  );
}

/** The stored shape of a question, built locally while its turn streams. */
export function questionContent(text: string, files: readonly ChatFile[]): AGUIMessage["content"] {
  if (files.length === 0) return text;
  const fileParts = files.map((file) => ({
    type: file.kind === "image" ? "image" : "document",
    id: file.id,
    source: { type: "url", value: `${STORED_FILE}${file.id}`, mimeType: file.content_type },
    metadata: { filename: file.original_name, sizeBytes: file.size_bytes },
  }));
  return [...(text ? [{ type: "text", text }] : []), ...fileParts] as AGUIMessage["content"];
}

/** A question's content with new text and the same files. */
export function withText(message: AGUIMessage | undefined, text: string): AGUIMessage["content"] {
  const files = parts(message).filter((part) => part.type !== "text");
  if (files.length === 0) return text;
  return [...(text ? [{ type: "text", text }] : []), ...files] as AGUIMessage["content"];
}

const SIZE_UNITS = ["B", "KB", "MB"];

export function formatBytes(bytes: number): string {
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < SIZE_UNITS.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${unit === 0 ? value : value.toFixed(1)} ${SIZE_UNITS[unit]}`;
}

/** Name of the tool that writes a file into the answer (D06). */
export const CREATE_FILE_TOOL = "create_file";

/** The file a `create_file` call made, from its JSON result; null otherwise
 * (another tool, a refusal, or no result yet). */
export function madeFile(toolName: string, result: unknown): AttachedFile | null {
  if (toolName !== CREATE_FILE_TOOL || typeof result !== "string") return null;
  try {
    const made = JSON.parse(result) as Record<string, unknown>;
    if (typeof made.file_id !== "string" || typeof made.name !== "string") return null;
    return {
      id: made.file_id,
      name: made.name,
      contentType: typeof made.content_type === "string" ? made.content_type : "",
      sizeBytes: typeof made.size_bytes === "number" ? made.size_bytes : 0,
      isImage: false,
    };
  } catch {
    return null;
  }
}
