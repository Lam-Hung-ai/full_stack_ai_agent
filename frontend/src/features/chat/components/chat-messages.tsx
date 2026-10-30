"use client";

import { useState } from "react";
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
import { buildTurns, findToolResult, parseToolArgs, type Turn } from "../utils/agui-messages";
import { isActive, isTerminal } from "../utils/history";
import { BranchSwitcher } from "./branch-switcher";
import { EditQuestionForm } from "./edit-question-form";
import { ReasoningSummary } from "./reasoning-summary";

export type RowActions = {
  onEdit: (userMessageId: string, text: string) => void;
  onRegenerate: (assistantMessageId: string) => void;
  onSwitch: (messageId: string) => void;
};

/**
 * The rendered branch, one SQL row at a time; `empty` shows when there are
 * none. Without `actions` the rows are read-only.
 */
export function ChatMessages({
  rows,
  isBusy,
  actions,
  empty,
}: {
  rows: readonly RowView[];
  isBusy: boolean;
  actions?: RowActions;
  empty?: React.ReactNode;
}) {
  return (
    <Conversation>
      <ConversationContent>
        {rows.length === 0
          ? empty
          : rows.map((row) =>
              row.role === "user" ? (
                <QuestionRow actions={actions} disabled={isBusy} key={row.id} row={row} />
              ) : (
                <AnswerRow
                  actions={actions}
                  disabled={isBusy}
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

function questionText(row: RowView): string {
  const message = row.content.find((item) => item.role === "user");
  return typeof message?.content === "string" ? message.content : "";
}

function QuestionRow({
  row,
  actions,
  disabled,
}: {
  row: RowView;
  actions?: RowActions;
  disabled: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const text = questionText(row);

  if (editing && actions) {
    return (
      <EditQuestionForm
        defaultText={text}
        onCancel={() => setEditing(false)}
        onSubmit={(edited) => {
          setEditing(false);
          actions.onEdit(row.id, edited);
        }}
      />
    );
  }
  return (
    <Message from="user">
      <MessageContent>
        <MessageResponse>{text}</MessageResponse>
      </MessageContent>
      {actions && (
        <MessageActions className="justify-end">
          <BranchSwitcher
            currentId={row.id}
            disabled={disabled}
            onSwitch={actions.onSwitch}
            siblingIds={row.siblingIds}
          />
          <MessageAction disabled={disabled} label="Sửa câu hỏi" onClick={() => setEditing(true)}>
            <PencilIcon />
          </MessageAction>
        </MessageActions>
      )}
    </Message>
  );
}

function AnswerRow({
  row,
  actions,
  disabled,
  isStreaming,
}: {
  row: RowView;
  actions?: RowActions;
  disabled: boolean;
  isStreaming: boolean;
}) {
  const turns = buildTurns(row.content);
  // Content is saved when a turn ends: one running elsewhere has none yet.
  const waiting = isStreaming || (!row.live && isActive(row));
  const showActions = actions && !row.live && isTerminal(row);

  return (
    <>
      {turns.length === 0 && waiting && (
        <Message from="assistant">
          <MessageContent>
            <Loader />
          </MessageContent>
        </Message>
      )}
      {turns.map((turn, index) => (
        <TurnView
          isStreaming={isStreaming && index === turns.length - 1}
          key={turn.message.id}
          messages={row.content}
          turn={turn}
        />
      ))}
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
              <MessageAction
                disabled={disabled}
                label="Tạo lại câu trả lời"
                onClick={() => actions.onRegenerate(row.id)}
              >
                <RefreshCcwIcon />
              </MessageAction>
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

function TurnView({
  turn: { message, reasoning },
  messages,
  isStreaming,
}: {
  turn: Turn;
  messages: readonly AGUIMessage[];
  isStreaming: boolean;
}) {
  if (message.role !== "assistant") return null;

  const toolCalls = message.toolCalls ?? [];
  const isReasoningStreaming = isStreaming && !message.content && toolCalls.length === 0;

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
          const state: ToolUIPart["state"] = result
            ? result.error
              ? "output-error"
              : "output-available"
            : "input-available";

          return (
            <Tool key={toolCall.id}>
              <ToolHeader state={state} type={`tool-${toolCall.function.name}` as ToolUIPart["type"]} />
              <ToolContent>
                <ToolInput input={parseToolArgs(toolCall.function.arguments)} />
                <ToolOutput
                  errorText={result?.error}
                  output={typeof result?.content === "string" ? result.content : undefined}
                />
              </ToolContent>
            </Tool>
          );
        })}
      </MessageContent>
    </Message>
  );
}
