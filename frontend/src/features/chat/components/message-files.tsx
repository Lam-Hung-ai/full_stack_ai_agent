"use client";

import { useState } from "react";
import { FileIcon } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { type FileLink, getFileLink } from "../api/files-api";
import { cn } from "@/lib/utils";
import { chatKeys } from "../hooks/use-conversations";
import { type AttachedFile, formatBytes } from "../utils/files";

/** Where links to a message's files come from: the owner's chat or a share. */
export type FileLinkSource = {
  key: readonly unknown[];
  fetch: (fileId: string, signal?: AbortSignal) => Promise<FileLink>;
};

/** Files of the owner's own chat. */
export function conversationFiles(conversationId: string): FileLinkSource {
  return {
    key: chatKeys.conversation(conversationId),
    fetch: (fileId, signal) => getFileLink(conversationId, fileId, signal),
  };
}

/** Links are signed for ten minutes; reuse one for less than that. */
const LINK_STALE_TIME = 5 * 60_000;

/** Files of a message: pictures inline, other files as links. */
export function MessageFiles({
  source,
  files,
  align = "end",
}: {
  source: FileLinkSource;
  files: readonly AttachedFile[];
  /** End for a question's attachments, start for files in an answer. */
  align?: "start" | "end";
}) {
  if (files.length === 0) return null;
  return (
    <div
      className={cn("flex flex-wrap gap-2", align === "end" ? "justify-end" : "justify-start")}
    >
      {files.map((file) =>
        file.isImage ? (
          <FileImage file={file} key={file.id} source={source} />
        ) : (
          <FileButton file={file} key={file.id} source={source} />
        ),
      )}
    </div>
  );
}

function linkQuery(source: FileLinkSource, fileId: string) {
  return {
    queryKey: [...source.key, "files", fileId] as const,
    queryFn: ({ signal }: { signal: AbortSignal }) => source.fetch(fileId, signal),
    staleTime: LINK_STALE_TIME,
  };
}

/** Opens a file with a link fresh enough to work (a shown one may be old). */
function useOpenFile(source: FileLinkSource, file: AttachedFile) {
  const queryClient = useQueryClient();
  const [failed, setFailed] = useState(false);
  const open = async () => {
    setFailed(false);
    try {
      const link = await queryClient.fetchQuery(linkQuery(source, file.id));
      // A new tab, never as the app's origin.
      window.open(link.url, "_blank", "noopener,noreferrer");
    } catch {
      setFailed(true);
    }
  };
  return { open, failed };
}

function FileImage({ source, file }: { source: FileLinkSource; file: AttachedFile }) {
  // Refreshed before the signed link expires while the chat stays open.
  const link = useQuery({ ...linkQuery(source, file.id), refetchInterval: LINK_STALE_TIME });
  const { open, failed } = useOpenFile(source, file);
  if (!link.data) {
    return link.isError ? (
      <FileButton file={file} source={source} />
    ) : (
      <div aria-busy className="size-32 animate-pulse rounded-md bg-muted" />
    );
  }
  return (
    <button className="flex flex-col items-end gap-1" onClick={() => void open()} type="button">
      {/* eslint-disable-next-line @next/next/no-img-element -- a presigned URL, not a static asset */}
      <img alt={file.name} className="max-h-48 max-w-64 rounded-md border object-contain" src={link.data.url} />
      {failed && <OpenFailed />}
    </button>
  );
}

function FileButton({ source, file }: { source: FileLinkSource; file: AttachedFile }) {
  const { open, failed } = useOpenFile(source, file);
  return (
    <button
      className="flex max-w-64 items-center gap-2 rounded-md border bg-muted/40 px-3 py-2 text-left text-sm hover:bg-muted"
      onClick={() => void open()}
      type="button"
    >
      <FileIcon className="size-4 shrink-0" />
      <span className="min-w-0">
        <span className="block truncate">{file.name}</span>
        <span className="text-muted-foreground text-xs">{formatBytes(file.sizeBytes)}</span>
        {failed && <OpenFailed />}
      </span>
    </button>
  );
}

function OpenFailed() {
  return <span className="block text-destructive text-xs">Không mở được tệp, thử lại sau.</span>;
}
