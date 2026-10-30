"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/lib/api";
import { StorageUploadError, uploadPresignedFile } from "@/lib/storage/upload";
import { type ChatFile, completeUpload, createUpload } from "../api/files-api";
import { contentTypeOf, MAX_FILE_BYTES, MAX_FILES } from "../utils/files";

export type Attachment = {
  localId: string;
  name: string;
  status: "uploading" | "ready" | "failed";
  file?: ChatFile;
  error?: string;
};

const ERRORS: Record<string, string> = {
  unsupported_file_type: "Loại tệp này chưa được hỗ trợ.",
  file_content_mismatch: "Nội dung tệp không đúng với loại tệp.",
  upload_size_mismatch: "Tệp tải lên không trọn vẹn.",
  storage_unavailable: "Kho tệp đang không sẵn sàng.",
  storage_upload_unreachable: "Không gửi được tệp tới kho lưu trữ.",
  storage_upload_rejected: "Kho lưu trữ từ chối tệp.",
  too_large: "Tệp lớn hơn 10 MB.",
};

function uploadError(error: unknown): string {
  const code =
    error instanceof ApiError || error instanceof StorageUploadError ? error.code : null;
  return (code && ERRORS[code]) || "Không tải được tệp.";
}

/**
 * Files picked in the composer, uploaded as soon as they are picked: an
 * error shows on the file while the typed question stays. Each upload is
 * the presigned flow: ask, PUT straight to storage, complete.
 */
export function useAttachments(workspaceId: string | undefined) {
  const [items, setItems] = useState<Attachment[]>([]);
  const controllers = useRef(new Map<string, AbortController>());

  useEffect(() => {
    const pending = controllers.current;
    return () => pending.forEach((controller) => controller.abort());
  }, []);

  const update = (localId: string, change: Partial<Attachment>) =>
    setItems((current) =>
      current.map((item) => (item.localId === localId ? { ...item, ...change } : item)),
    );

  const upload = useCallback(
    async (localId: string, file: File) => {
      if (!workspaceId) return;
      if (file.size > MAX_FILE_BYTES) {
        update(localId, { status: "failed", error: ERRORS.too_large });
        return;
      }
      const controller = new AbortController();
      controllers.current.set(localId, controller);
      const declared = {
        original_name: file.name,
        content_type: contentTypeOf(file),
        size_bytes: file.size,
      };
      try {
        const ticket = await createUpload(workspaceId, declared);
        await uploadPresignedFile(file, ticket.upload, controller.signal);
        const stored = await completeUpload(workspaceId, ticket.file_id, declared);
        update(localId, { status: "ready", file: stored });
      } catch (error) {
        if (controller.signal.aborted) return;
        update(localId, { status: "failed", error: uploadError(error) });
      } finally {
        controllers.current.delete(localId);
      }
    },
    [workspaceId],
  );

  const add = useCallback(
    (files: FileList | File[]) => {
      const room = MAX_FILES - items.length;
      const picked = Array.from(files)
        .slice(0, Math.max(room, 0))
        .map((file) => ({ file, localId: crypto.randomUUID() }));
      setItems((current) => [
        ...current,
        ...picked.map(({ file, localId }) => ({
          localId,
          name: file.name,
          status: "uploading" as const,
        })),
      ]);
      for (const { file, localId } of picked) void upload(localId, file);
    },
    [items.length, upload],
  );

  const remove = useCallback((localId: string) => {
    controllers.current.get(localId)?.abort();
    setItems((current) => current.filter((item) => item.localId !== localId));
  }, []);

  const clear = useCallback(() => setItems([]), []);

  return {
    items,
    add,
    remove,
    clear,
    isUploading: items.some((item) => item.status === "uploading"),
    ready: items.flatMap((item) => (item.status === "ready" && item.file ? [item.file] : [])),
    canAdd: items.length < MAX_FILES,
  };
}
