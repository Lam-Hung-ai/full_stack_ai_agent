"use client";

import { useState } from "react";
import { FileTextIcon } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Attachment,
  AttachmentContent,
  AttachmentDescription,
  AttachmentMedia,
  AttachmentTitle,
  AttachmentTrigger,
} from "@/components/ui/attachment";
import { type FileLink, getFileLink } from "../api/files-api";
import { cn } from "@/lib/utils";
import { chatKeys } from "../hooks/use-conversations";
import { type AttachedFile, fileLabel } from "../utils/files";

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
    <div className={cn("flex flex-wrap gap-2", align === "end" ? "justify-end" : "justify-start")}>
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
      <img
        alt={file.name}
        className="max-h-56 max-w-72 rounded-xl border object-contain"
        src={link.data.url}
      />
      {failed && <OpenFailed />}
    </button>
  );
}

function FileButton({ source, file }: { source: FileLinkSource; file: AttachedFile }) {
  const { open, failed } = useOpenFile(source, file);
  return (
    <Attachment className="max-w-72" state={failed ? "error" : "done"} title={file.name}>
      <AttachmentMedia>
        <FileTextIcon />
      </AttachmentMedia>
      <AttachmentContent>
        <AttachmentTitle>{file.name}</AttachmentTitle>
        <AttachmentDescription>
          {failed ? "Không mở được tệp, thử lại sau." : fileLabel(file.name, file.sizeBytes)}
        </AttachmentDescription>
      </AttachmentContent>
      <AttachmentTrigger aria-label={`Mở ${file.name}`} onClick={() => void open()} />
    </Attachment>
  );
}

function OpenFailed() {
  return <span className="block text-destructive text-xs">Không mở được tệp, thử lại sau.</span>;
}
