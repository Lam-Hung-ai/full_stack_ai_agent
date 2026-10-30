"use client";

import { FileIcon } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getFileLink } from "../api/files-api";
import { chatKeys } from "../hooks/use-conversations";
import { type AttachedFile, formatBytes } from "../utils/files";

/** Links are signed for ten minutes; reuse one for less than that. */
const LINK_STALE_TIME = 5 * 60_000;

/** Files attached to a question: pictures inline, other files as links. */
export function MessageFiles({
  conversationId,
  files,
}: {
  conversationId: string;
  files: readonly AttachedFile[];
}) {
  if (files.length === 0) return null;
  return (
    <div className="flex flex-wrap justify-end gap-2">
      {files.map((file) =>
        file.isImage ? (
          <FileImage conversationId={conversationId} file={file} key={file.id} />
        ) : (
          <FileLink conversationId={conversationId} file={file} key={file.id} />
        ),
      )}
    </div>
  );
}

function linkQuery(conversationId: string, fileId: string) {
  return {
    queryKey: [...chatKeys.conversation(conversationId), "files", fileId] as const,
    queryFn: ({ signal }: { signal: AbortSignal }) => getFileLink(conversationId, fileId, signal),
    staleTime: LINK_STALE_TIME,
  };
}

function FileImage({ conversationId, file }: { conversationId: string; file: AttachedFile }) {
  const link = useQuery(linkQuery(conversationId, file.id));
  if (!link.data) {
    return <div aria-busy className="size-32 animate-pulse rounded-md bg-muted" />;
  }
  return (
    <a href={link.data.url} rel="noopener noreferrer" target="_blank">
      {/* eslint-disable-next-line @next/next/no-img-element -- a presigned URL, not a static asset */}
      <img alt={file.name} className="max-h-48 max-w-64 rounded-md border object-contain" src={link.data.url} />
    </a>
  );
}

function FileLink({ conversationId, file }: { conversationId: string; file: AttachedFile }) {
  const queryClient = useQueryClient();
  const open = async () => {
    // A fresh link on demand; opened in a new tab, never as the app's origin.
    const link = await queryClient.fetchQuery(linkQuery(conversationId, file.id));
    window.open(link.url, "_blank", "noopener,noreferrer");
  };
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
      </span>
    </button>
  );
}
