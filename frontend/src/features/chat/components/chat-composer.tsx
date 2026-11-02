"use client";

import { useEffect, useRef } from "react";
import type { ChatStatus } from "ai";
import { FileTextIcon, PaperclipIcon, TriangleAlertIcon, XIcon } from "lucide-react";
import {
  PromptInput,
  PromptInputBody,
  PromptInputButton,
  PromptInputFooter,
  PromptInputHeader,
  PromptInputProvider,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools,
  useProviderAttachments,
} from "@/components/ai-elements/prompt-input";
import {
  Attachment,
  AttachmentAction,
  AttachmentActions,
  AttachmentContent,
  AttachmentDescription,
  AttachmentGroup,
  AttachmentMedia,
  AttachmentTitle,
} from "@/components/ui/attachment";
import { Spinner } from "@/components/ui/spinner";
import type { ChatFile } from "../api/files-api";
import { type Attachment as Picked, useAttachments } from "../hooks/use-attachments";
import { ACCEPTED_FILES, fileLabel } from "../utils/files";

export type ComposerDraft = { text: string; files: ChatFile[] };

/** The composer's column under the messages, with the usual caution below it. */
export function ChatFooter({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-2 px-4 pb-2">
      {children}
      <p className="text-center text-muted-foreground text-xs">
        AI có thể mắc lỗi. Hãy kiểm tra lại thông tin quan trọng.
      </p>
    </div>
  );
}

export function ChatComposer({
  workspaceId,
  status,
  disabled,
  placeholder = "Trả lời…",
  onSubmit,
  onStop,
}: {
  /** Where picked files are uploaded; without it files cannot be attached. */
  workspaceId?: string;
  status: ChatStatus;
  disabled?: boolean;
  placeholder?: string;
  /** True once the question is taken; the draft stays until then and on failure. */
  onSubmit: (draft: ComposerDraft) => Promise<boolean>;
  /** Given while an answer can be stopped: the submit button becomes "Dừng". */
  onStop?: () => void;
}) {
  const attachments = useAttachments(workspaceId);
  const picker = useRef<HTMLInputElement>(null);
  // Nothing is sent while blocked (a turn runs or waits, files upload), and
  // the typed text stays. Enter submits even when only "Dừng" is shown.
  const blocked = disabled || attachments.isUploading;

  return (
    // The provider keeps the text until onSubmit resolves; a rejection keeps it.
    <PromptInputProvider>
      <DroppedFiles onFiles={workspaceId && attachments.canAdd ? attachments.add : undefined} />
      <PromptInput
        className="*:data-[slot=input-group]:rounded-2xl *:data-[slot=input-group]:bg-background *:data-[slot=input-group]:shadow-sm"
        onSubmit={async (message) => {
          if (blocked || (!message.text.trim() && attachments.ready.length === 0)) {
            throw new Error("not sent");
          }
          if (!(await onSubmit({ text: message.text, files: attachments.ready }))) {
            throw new Error("not sent");
          }
          attachments.clear();
        }}
      >
        {attachments.items.length > 0 && (
          <PromptInputHeader>
            <AttachmentGroup className="w-full">
              {attachments.items.map((item) => (
                <AttachmentChip
                  item={item}
                  key={item.localId}
                  onRemove={() => attachments.remove(item.localId)}
                />
              ))}
            </AttachmentGroup>
          </PromptInputHeader>
        )}
        <PromptInputBody>
          <PromptInputTextarea className="text-[0.9375rem]" placeholder={placeholder} />
        </PromptInputBody>
        <PromptInputFooter>
          <PromptInputTools>
            {workspaceId && (
              <>
                <PromptInputButton
                  aria-label="Đính kèm tệp"
                  disabled={!attachments.canAdd}
                  onClick={() => picker.current?.click()}
                  title="Đính kèm tệp (hoặc dán, kéo thả vào đây)"
                >
                  <PaperclipIcon className="size-4" />
                </PromptInputButton>
                <input
                  accept={ACCEPTED_FILES}
                  aria-hidden
                  className="hidden"
                  multiple
                  onChange={(event) => {
                    if (event.currentTarget.files) attachments.add(event.currentTarget.files);
                    // Picking the same file again must fire a change.
                    event.currentTarget.value = "";
                  }}
                  ref={picker}
                  tabIndex={-1}
                  type="file"
                />
              </>
            )}
          </PromptInputTools>
          {onStop ? (
            <PromptInputSubmit
              aria-label="Dừng"
              onClick={onStop}
              status="streaming"
              type="button"
            />
          ) : (
            <PromptInputSubmit disabled={blocked} status={status} />
          )}
        </PromptInputFooter>
      </PromptInput>
    </PromptInputProvider>
  );
}

/**
 * Files pasted into or dropped on the prompt land in the AI Elements
 * provider as blob URLs; hand each to our uploads once, then drop it there.
 * Without `onFiles` (no workspace, or full) they are dropped unused.
 */
function DroppedFiles({ onFiles }: { onFiles?: (files: File[]) => void }) {
  const { files, remove } = useProviderAttachments();
  const taken = useRef(new Set<string>());
  const latest = useRef(onFiles);
  useEffect(() => {
    latest.current = onFiles;
  }, [onFiles]);

  useEffect(() => {
    const fresh = files.filter((part) => !taken.current.has(part.id));
    if (fresh.length === 0) return;
    for (const part of fresh) taken.current.add(part.id);
    void Promise.all(
      fresh.map(async (part) => {
        try {
          const blob = await (await fetch(part.url)).blob();
          return new File([blob], part.filename || "tệp", { type: part.mediaType || blob.type });
        } catch {
          return null;
        } finally {
          // Revokes the blob URL; read above first. The id stays taken: the
          // list may still show it for a render before the removal lands.
          remove(part.id);
        }
      }),
    ).then((read) => {
      const ready = read.filter((file): file is File => file !== null);
      if (ready.length > 0) latest.current?.(ready);
    });
  }, [files, remove]);

  return null;
}

const STATE = { uploading: "uploading", failed: "error", ready: "done" } as const;

function AttachmentChip({ item, onRemove }: { item: Picked; onRemove: () => void }) {
  return (
    <Attachment
      className="max-w-64"
      size="sm"
      state={STATE[item.status]}
      title={item.error ?? item.name}
    >
      <AttachmentMedia variant={item.previewUrl ? "image" : "icon"}>
        {item.previewUrl ? (
          // eslint-disable-next-line @next/next/no-img-element -- a local object URL
          <img alt="" src={item.previewUrl} />
        ) : item.status === "uploading" ? (
          <Spinner aria-label="Đang tải lên" />
        ) : item.status === "failed" ? (
          <TriangleAlertIcon />
        ) : (
          <FileTextIcon />
        )}
      </AttachmentMedia>
      <AttachmentContent>
        <AttachmentTitle>{item.name}</AttachmentTitle>
        <AttachmentDescription>
          {item.error ??
            (item.status === "uploading" ? "Đang tải lên…" : fileLabel(item.name, item.sizeBytes))}
        </AttachmentDescription>
      </AttachmentContent>
      <AttachmentActions>
        <AttachmentAction aria-label={`Bỏ ${item.name}`} onClick={onRemove} type="button">
          <XIcon />
        </AttachmentAction>
      </AttachmentActions>
    </Attachment>
  );
}
