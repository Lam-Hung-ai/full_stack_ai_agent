"use client";

import { useRef } from "react";
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
import { ACCEPTED_FILES, fileLabel, filesOf } from "../utils/files";

export type ComposerDraft = { text: string; files: ChatFile[] };

/** The composer's column under the messages, with the usual caution below it. */
export function ChatFooter({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-2 px-4 pb-2">
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
  placeholder = "Hỏi agent",
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

  // Pasted (Ctrl+V of a screenshot or of files copied in a file manager) or
  // dropped files go to our own uploads, never to AI Elements' attachment
  // list, which only keeps blob URLs. True when the event carried files.
  const takeFiles = (data: DataTransfer | null) => {
    const files = filesOf(data);
    if (files.length === 0 || !workspaceId) return false;
    if (attachments.canAdd) attachments.add(files);
    return true;
  };

  return (
    // The provider keeps the text until onSubmit resolves; a rejection keeps it.
    <PromptInputProvider>
      <div
        // Capture: runs before PromptInput's own drop listener on its form.
        onDropCapture={(event) => {
          if (!takeFiles(event.dataTransfer)) return;
          event.preventDefault();
          event.stopPropagation();
        }}
      >
        <PromptInput
          className="*:data-[slot=input-group]:rounded-2xl *:data-[slot=input-group]:bg-background *:data-[slot=input-group]:shadow-xs"
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
            <PromptInputHeader className="pb-0">
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
            <PromptInputTextarea
              // 14px like the sent question; 16px on phones, where smaller
              // text makes iPhones zoom in on focus.
              className="min-h-10 py-2.5 text-base md:text-sm"
              onPaste={(event) => takeFiles(event.clipboardData) && event.preventDefault()}
              placeholder={placeholder}
            />
          </PromptInputBody>
          <PromptInputFooter className="pt-0 pb-1.5">
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
      </div>
    </PromptInputProvider>
  );
}

const STATE = { uploading: "uploading", failed: "error", ready: "done" } as const;

function AttachmentChip({ item, onRemove }: { item: Picked; onRemove: () => void }) {
  return (
    <Attachment
      className="max-w-56"
      size="xs"
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
