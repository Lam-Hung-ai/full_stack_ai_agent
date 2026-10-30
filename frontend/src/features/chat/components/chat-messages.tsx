"use client";

import { Fragment, useState } from "react";
import type { Message as AGUIMessage } from "@ag-ui/client";
import type { ToolUIPart } from "ai";
import { PencilIcon, RefreshCcwIcon } from "lucide-react";
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import { Loader } from "@/components/ai-elements/loader";
import {
  Message,
  MessageAction,
  MessageActions,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
import { Reasoning, ReasoningContent, ReasoningTrigger } from "@/components/ai-elements/reasoning";
import { Tool, ToolContent, ToolHeader, ToolInput, ToolOutput } from "@/components/ai-elements/tool";
import type { RowView } from "../types/chat.types";
import { buildItems, findToolResult, parseToolArgs, type Turn } from "../utils/agui-messages";
import { isActive, isTerminal } from "../utils/history";
import { attachedFiles, madeFile, questionText as textOf } from "../utils/files";
import { ASK_USER_TOOL, type InteractionAnswer, interactionOf } from "../utils/interactions";
import { BranchSwitcher } from "./branch-switcher";
import { EditQuestionForm } from "./edit-question-form";
import { InteractionCard } from "./interaction-card";
import { type FileLinkSource, MessageFiles } from "./message-files";
import { ReasoningSummary } from "./reasoning-summary";

/** What the reader may do; a shared snapshot only switches versions. */
export type RowActions = {
  onSwitch: (messageId: string) => void;
  onEdit?: (userMessageId: string, text: string) => void;
  onRegenerate?: (assistantMessageId: string) => void;
  onAnswer?: (assistantMessageId: string, interruptId: string, answer: InteractionAnswer) => void;
  /** Answers kept until every question of a pause has one, by interrupt id. */
  drafts?: Record<string, InteractionAnswer>;
};

/**
 * The rendered branch, one SQL row at a time; `empty` shows when there are
 * none. Without `actions` the rows are read-only.
 */
export function ChatMessages({
  fileSource,
  rows,
  isBusy,
  waitingForUser = false,
  actions,
  empty,
}: {
  /** Where attached files open from; absent before the chat exists. */
  fileSource?: FileLinkSource;
  rows: readonly RowView[];
  isBusy: boolean;
  /** A pause holds the chat: only its questions can be acted on. */
  waitingForUser?: boolean;
  actions?: RowActions;
  empty?: React.ReactNode;
}) {
  const locked = isBusy || waitingForUser;
  return (
    <Conversation>
      <ConversationContent>
        {rows.length === 0
          ? empty
          : rows.map((row) =>
              row.role === "user" ? (
                <QuestionRow
                  actions={actions}
                  disabled={locked}
                  fileSource={fileSource}
                  key={row.id}
                  row={row}
                />
              ) : (
                <AnswerRow
                  actions={actions}
                  answerable={!isBusy}
                  disabled={locked}
                  fileSource={fileSource}
                  isStreaming={isBusy && !!row.live}
                  key={row.id}
                  row={row}
                />
              ),
            )}
      </ConversationContent>
      <ConversationScrollButton />
    </Conversation>
  );
}

function QuestionRow({
  row,
  actions,
  fileSource,
  disabled,
}: {
  row: RowView;
  actions?: RowActions;
  fileSource?: FileLinkSource;
  disabled: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const question = row.content.find((item) => item.role === "user");
  const text = textOf(question);
  const files = attachedFiles(question);

  const onEdit = actions?.onEdit;
  if (editing && onEdit) {
    return (
      <EditQuestionForm
        defaultText={text}
        onCancel={() => setEditing(false)}
        onSubmit={(edited) => {
          setEditing(false);
          onEdit(row.id, edited);
        }}
      />
    );
  }
  return (
    <Message from="user">
      {fileSource && <MessageFiles files={files} source={fileSource} />}
      {text && (
        <MessageContent>
          <MessageResponse>{text}</MessageResponse>
        </MessageContent>
      )}
      {actions && (
        <MessageActions className="justify-end">
          <BranchSwitcher
            currentId={row.id}
            disabled={disabled}
            onSwitch={actions.onSwitch}
            siblingIds={row.siblingIds}
          />
          {onEdit && (
            <MessageAction disabled={disabled} label="Sửa câu hỏi" onClick={() => setEditing(true)}>
              <PencilIcon />
            </MessageAction>
          )}
        </MessageActions>
      )}
    </Message>
  );
}

function AnswerRow({
  row,
  actions,
  answerable,
  disabled,
  fileSource,
  isStreaming,
}: {
  row: RowView;
  actions?: RowActions;
  answerable: boolean;
  disabled: boolean;
  fileSource?: FileLinkSource;
  isStreaming: boolean;
}) {
  const items = buildItems(row.content);
  // Content is saved when a turn ends: one running elsewhere has none yet.
  const waiting = isStreaming || (!row.live && isActive(row));
  const showActions = actions && !row.live && isTerminal(row);
  // Only a saved pause can be answered; the server checks it again.
  const onAnswer = answerable && !row.live && row.status === "requires_action" ? actions?.onAnswer : undefined;

  return (
    <>
      {items.length === 0 && waiting && (
        <Message from="assistant">
          <MessageContent>
            <Loader />
          </MessageContent>
        </Message>
      )}
      {items.map((item, index) => {
        if (item.kind === "turn") {
          return (
            <TurnView
              fileSource={fileSource}
              isStreaming={isStreaming && index === items.length - 1}
              key={item.turn.message.id}
              messages={row.content}
              rowStatus={row.live ? "running" : row.status}
              turn={item.turn}
            />
          );
        }
        const interaction = interactionOf(item.message);
        if (!interaction) return null;
        return (
          <Message from="assistant" key={item.message.id}>
            <InteractionCard
              draft={actions?.drafts?.[interaction.interrupt_id]}
              interaction={interaction}
              onAnswer={
                onAnswer
                  ? (answer) => onAnswer(row.id, interaction.interrupt_id, answer)
                  : undefined
              }
            />
          </Message>
        );
      })}
      {(row.status === "cancelled" || row.status === "failed" || showActions) && (
        <MessageActions>
          {row.status === "cancelled" && (
            <span className="px-1 text-muted-foreground text-xs">Đã dừng</span>
          )}
          {row.status === "failed" && (
            <span className="px-1 text-destructive text-xs">Câu trả lời chưa hoàn tất do lỗi</span>
          )}
          {showActions && (
            <>
              {actions.onRegenerate && (
                <MessageAction
                  disabled={disabled}
                  label="Tạo lại câu trả lời"
                  onClick={() => actions.onRegenerate?.(row.id)}
                >
                  <RefreshCcwIcon />
                </MessageAction>
              )}
              <BranchSwitcher
                currentId={row.id}
                disabled={disabled}
                onSwitch={actions.onSwitch}
                siblingIds={row.siblingIds}
              />
            </>
          )}
        </MessageActions>
      )}
    </>
  );
}

/** A tool call with no result yet, by where its turn stands. */
const PENDING_TOOL_STATE: Partial<Record<RowView["status"], ToolUIPart["state"]>> = {
  requires_action: "approval-requested",
  cancelled: "output-denied",
  failed: "output-error",
};

function TurnView({
  turn: { message, reasoning },
  messages,
  rowStatus,
  fileSource,
  isStreaming,
}: {
  turn: Turn;
  messages: readonly AGUIMessage[];
  rowStatus: RowView["status"];
  fileSource?: FileLinkSource;
  isStreaming: boolean;
}) {
  if (message.role !== "assistant") return null;

  // ask_user shows as its interaction card, not as a tool call.
  const toolCalls = (message.toolCalls ?? []).filter(
    (call) => call.function.name !== ASK_USER_TOOL,
  );
  const isReasoningStreaming = isStreaming && !message.content && toolCalls.length === 0;
  if (!reasoning && !message.content && toolCalls.length === 0 && !isStreaming) return null;

  return (
    <Message from="assistant">
      <MessageContent>
        {reasoning && (
          <Reasoning defaultOpen={isReasoningStreaming} isStreaming={isReasoningStreaming}>
            <ReasoningTrigger>
              <ReasoningSummary isStreaming={isReasoningStreaming} reasoning={reasoning} />
            </ReasoningTrigger>
            <ReasoningContent>{reasoning}</ReasoningContent>
          </Reasoning>
        )}
        {message.content ? (
          <MessageResponse>{message.content}</MessageResponse>
        ) : toolCalls.length === 0 && !reasoning && isStreaming ? (
          <Loader />
        ) : null}
        {toolCalls.map((toolCall) => {
          const result = findToolResult(messages, toolCall.id);
          const made = madeFile(toolCall.function.name, result?.content);
          const state: ToolUIPart["state"] = result
            ? result.error
              ? "output-error"
              : "output-available"
            : (PENDING_TOOL_STATE[rowStatus] ?? "input-available");

          return (
            <Fragment key={toolCall.id}>
              <Tool>
                <ToolHeader
                  state={state}
                  type={`tool-${toolCall.function.name}` as ToolUIPart["type"]}
                />
                <ToolContent>
                  <ToolInput input={parseToolArgs(toolCall.function.arguments)} />
                  <ToolOutput
                    errorText={result?.error}
                    output={typeof result?.content === "string" ? result.content : undefined}
                  />
                </ToolContent>
              </Tool>
              {made && fileSource && (
                <MessageFiles align="start" files={[made]} source={fileSource} />
              )}
            </Fragment>
          );
        })}
      </MessageContent>
    </Message>
  );
}
