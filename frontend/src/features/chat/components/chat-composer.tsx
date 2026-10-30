"use client";

import { useRef } from "react";
import type { ChatStatus } from "ai";
import {
  FileIcon,
  Loader2Icon,
  PaperclipIcon,
  TriangleAlertIcon,
  XIcon,
} from "lucide-react";
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
} from "@/components/ai-elements/prompt-input";
import { Button } from "@/components/ui/button";
import type { ChatFile } from "../api/files-api";
import { type Attachment, useAttachments } from "../hooks/use-attachments";
import { ACCEPTED_FILES } from "../utils/files";

export type ComposerDraft = { text: string; files: ChatFile[] };

export function ChatComposer({
  workspaceId,
  status,
  disabled,
  onSubmit,
  onStop,
}: {
  /** Where picked files are uploaded; without it files cannot be attached. */
  workspaceId?: string;
  status: ChatStatus;
  disabled?: boolean;
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
      <PromptInput
        className="mt-4"
        onSubmit={async (message) => {
          if (
            blocked ||
            (!message.text.trim() && attachments.ready.length === 0)
          ) {
            throw new Error("not sent");
          }
          if (
            !(await onSubmit({ text: message.text, files: attachments.ready }))
          ) {
            throw new Error("not sent");
          }
          attachments.clear();
        }}
      >
        {attachments.items.length > 0 && (
          <PromptInputHeader className="flex flex-wrap gap-2">
            {attachments.items.map((item) => (
              <AttachmentChip
                item={item}
                key={item.localId}
                onRemove={() => attachments.remove(item.localId)}
              />
            ))}
          </PromptInputHeader>
        )}
        <PromptInputBody>
          <PromptInputTextarea placeholder="Nhập câu hỏi…" />
        </PromptInputBody>
        <PromptInputFooter>
          <PromptInputTools>
            {workspaceId && (
              <>
                <PromptInputButton
                  aria-label="Đính kèm tệp"
                  disabled={!attachments.canAdd}
                  onClick={() => picker.current?.click()}
                >
                  <PaperclipIcon className="size-4" />
                </PromptInputButton>
                <input
                  accept={ACCEPTED_FILES}
                  aria-hidden
                  className="hidden"
                  multiple
                  onChange={(event) => {
                    if (event.currentTarget.files)
                      attachments.add(event.currentTarget.files);
                    // Picking the same file again must fire a change.
                    event.currentTarget.value = "";
                  }}
                  ref={picker}
                  tabIndex={-1}
                  type="file"
                />
              </>
            )}
            <span className="text-muted-foreground text-xs">
              Enter để gửi, Shift+Enter để xuống dòng
            </span>
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

function AttachmentChip({
  item,
  onRemove,
}: {
  item: Attachment;
  onRemove: () => void;
}) {
  return (
    <div
      className="flex max-w-56 items-center gap-1.5 rounded-md border bg-muted/40 py-1 pr-1 pl-2 text-xs"
      title={item.error ?? item.name}
    >
      {item.status === "uploading" ? (
        <Loader2Icon
          aria-label="Đang tải lên"
          className="size-3.5 shrink-0 animate-spin"
        />
      ) : item.status === "failed" ? (
        <TriangleAlertIcon
          aria-label="Lỗi"
          className="size-3.5 shrink-0 text-destructive"
        />
      ) : (
        <FileIcon className="size-3.5 shrink-0" />
      )}
      <span className="truncate">{item.name}</span>
      {item.error && (
        <span className="truncate text-destructive">· {item.error}</span>
      )}
      <Button
        aria-label={`Bỏ ${item.name}`}
        className="size-5"
        onClick={onRemove}
        size="icon"
        type="button"
        variant="ghost"
      >
        <XIcon className="size-3" />
      </Button>
    </div>
  );
}
