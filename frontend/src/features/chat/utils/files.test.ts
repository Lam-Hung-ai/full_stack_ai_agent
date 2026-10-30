import type { Message as AGUIMessage } from "@ag-ui/client";
import { describe, expect, it } from "vitest";
import {
  attachedFiles,
  madeFile,
  contentTypeOf,
  formatBytes,
  questionContent,
  questionText,
  withText,
} from "./files";

const image = {
  id: "f1",
  original_name: "ảnh.png",
  content_type: "image/png",
  size_bytes: 2048,
  kind: "image" as const,
};
const note = { ...image, id: "f2", original_name: "note.txt", content_type: "text/plain", kind: "text" as const };

function message(content: AGUIMessage["content"]): AGUIMessage {
  return { id: "m", role: "user", content } as AGUIMessage;
}

describe("question content", () => {
  it("keeps a plain question a string", () => {
    expect(questionContent("Chào", [])).toBe("Chào");
    expect(questionText(message("Chào"))).toBe("Chào");
  });

  it("round-trips files through the stored shape", () => {
    const stored = message(questionContent("Xem", [image, note]));
    expect(questionText(stored)).toBe("Xem");
    expect(attachedFiles(stored)).toEqual([
      { id: "f1", name: "ảnh.png", contentType: "image/png", sizeBytes: 2048, isImage: true },
      { id: "f2", name: "note.txt", contentType: "text/plain", sizeBytes: 2048, isImage: false },
    ]);
  });

  it("edits the text and keeps the files", () => {
    const edited = message(withText(message(questionContent("Cũ", [image])), "Mới"));
    expect(questionText(edited)).toBe("Mới");
    expect(attachedFiles(edited).map((file) => file.id)).toEqual(["f1"]);
  });
});

describe("helpers", () => {
  it("names content types from the extension when the browser does not", () => {
    expect(contentTypeOf({ name: "Ghi chú.MD", type: "" })).toBe("text/markdown");
    expect(contentTypeOf({ name: "x.bin", type: "application/octet-stream" })).toBe(
      "application/octet-stream",
    );
  });

  it("formats sizes", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(2048)).toBe("2.0 KB");
    expect(formatBytes(5 * 1024 * 1024)).toBe("5.0 MB");
  });
});

describe("madeFile", () => {
  const result = JSON.stringify({
    file_id: "f1",
    name: "Chi phí.xlsx",
    content_type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    size_bytes: 4096,
  });

  it("reads the file a create_file call made", () => {
    expect(madeFile("create_file", result)).toEqual({
      id: "f1",
      name: "Chi phí.xlsx",
      contentType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      sizeBytes: 4096,
      isImage: false,
    });
  });

  it("ignores other tools, refusals and missing results", () => {
    expect(madeFile("get_current_time", result)).toBeNull();
    expect(madeFile("create_file", "Could not create the file: too big")).toBeNull();
    expect(madeFile("create_file", undefined)).toBeNull();
  });
});
