"use client";

import { Fragment, useLayoutEffect, useState } from "react";
import { useStickToBottomContext } from "use-stick-to-bottom";
import type { Message as AGUIMessage } from "@ag-ui/client";
import type { ToolUIPart } from "ai";
import { PencilIcon, RefreshCcwIcon, RotateCcwIcon } from "lucide-react";
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
import {
  Tool,
  ToolContent,
  ToolHeader,
  ToolInput,
  ToolOutput,
} from "@/components/ai-elements/tool";
import { cn } from "@/lib/utils";
import type { RowView } from "../types/chat.types";
import {
  answerText,
  buildItems,
  findToolResult,
  parseToolArgs,
  type Turn,
} from "../utils/agui-messages";
import { isActive, isTerminal } from "../utils/history";
import { attachedFiles, madeFile, questionText as textOf } from "../utils/files";
import { turnTime, turnTimeTitle, workDuration } from "../utils/turn-time";
import { ASK_USER_TOOL, type InteractionAnswer, interactionOf } from "../utils/interactions";
import { BranchSwitcher } from "./branch-switcher";
import { CopyAction } from "./copy-action";
import { EditQuestionForm } from "./edit-question-form";
import { InteractionCard } from "./interaction-card";
import { type FileLinkSource, MessageFiles } from "./message-files";
import { ReasoningSummary } from "./reasoning-summary";

/**
 * Answer prose: 16px serif with relaxed leading; paragraphs, lists and
 * headings capped at 35em (about 70 characters a line), while tables and
 * code (wrapped in divs) keep the column width. Headings sit tighter.
 */
const ANSWER_CLASS = cn(
  "font-serif text-base leading-relaxed",
  "*:max-w-[35em] [&>div]:max-w-none [&>hr]:max-w-none",
  "[&_:is(h1,h2,h3)]:font-semibold [&_:is(h1,h2,h3)]:leading-tight",
  "[&_h1]:text-xl [&_h2]:text-lg [&_h3]:text-base",
  // Tables keep the answer's serif, a step smaller, with aligned digits.
  // Columns take their natural width (cells wrap past 18rem) and a wide
  // table scrolls, instead of squeezing a column to one word a line.
  "[&_table]:w-max [&_table]:min-w-full [&_table]:text-sm [&_table]:tabular-nums",
  "[&_:is(td,th)]:max-w-[18rem]",
  // Math in a cell at the cell's size; important because katex.min.css is
  // unlayered and beats every Tailwind layer.
  "[&_td_.katex]:text-[1em]!",
  // Inline code scales with the text around it (mono looks large per px).
  "[&_:not(pre)>code]:text-[0.875em]",
);

/** Turn footers: small, quiet icons. */
const FOOTER_CLASS = "gap-0 text-muted-foreground [&_button]:size-6 [&_svg]:size-3";

/** What the reader may do; a shared snapshot only switches versions. */
export type RowActions = {
  onSwitch: (turnId: string) => void;
  onEdit?: (userTurnId: string, text: string) => void;
  onRegenerate?: (assistantTurnId: string) => void;
  onAnswer?: (assistantTurnId: string, interruptId: string, answer: InteractionAnswer) => void;
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
    // Opens at the last turn at once, and follows growth without animating:
    // a smooth scroll down the whole chat on every load is hard on the eyes.
    <Conversation initial="instant" resize="instant">
      <ConversationContent className="mx-auto w-full max-w-3xl px-4 py-6">
        {rows.length === 0
          ? empty
          : rows.map((row, index) =>
              row.role === "user" ? (
                <QuestionRow
                  actions={actions}
                  answer={rows[index + 1]?.role === "assistant" ? rows[index + 1] : undefined}
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
      <OpenAtEnd />
      <ConversationScrollButton />
    </Conversation>
  );
}

function QuestionRow({
  row,
  answer,
  actions,
  fileSource,
  disabled,
}: {
  row: RowView;
  /** The answer below; "Thử lại" regenerates it. */
  answer?: RowView;
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
        <MessageContent className="text-sm group-[.is-user]:rounded-2xl">
          <MessageResponse>{text}</MessageResponse>
        </MessageContent>
      )}
      {/* Shown on hover (always on touch screens), like Claude. */}
      <MessageActions
        className={cn(
          FOOTER_CLASS,
          "justify-end transition-opacity focus-within:opacity-100 group-hover:opacity-100 md:opacity-0",
        )}
      >
        <TurnTime createdAt={row.createdAt} />
        {actions && (
          <BranchSwitcher
            currentId={row.id}
            disabled={disabled}
            onSwitch={actions.onSwitch}
            siblingIds={row.siblingIds}
          />
        )}
        {actions?.onRegenerate && answer && !answer.live && isTerminal(answer) && (
          <MessageAction
            disabled={disabled}
            label="Thử lại"
            onClick={() => actions.onRegenerate?.(answer.id)}
            tooltip="Thử lại"
          >
            <RotateCcwIcon />
          </MessageAction>
        )}
        {onEdit && (
          <MessageAction
            disabled={disabled}
            label="Sửa câu hỏi"
            onClick={() => setEditing(true)}
            tooltip="Sửa"
          >
            <PencilIcon />
          </MessageAction>
        )}
        {text && <CopyAction text={text} />}
      </MessageActions>
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
  const finished = !row.live && isTerminal(row);
  const showActions = actions && finished;
  const copyText = answerText(row.content);
  // Like ChatGPT's "Worked for 7s", on the answer's first thinking step.
  const workTime = finished ? workDuration(row.createdAt, row.updatedAt) : null;
  const firstThought = items.findIndex((item) => item.kind === "turn" && item.turn.reasoning);
  // Only a saved pause can be answered; the server checks it again.
  const onAnswer =
    answerable && !row.live && row.status === "requires_action" ? actions?.onAnswer : undefined;

  return (
    // One block, so the footer sits right under the answer instead of a
    // whole conversation gap below it.
    <div className="flex flex-col gap-2">
      {/* Steps of one answer sit closer than turns do (32px). */}
      <div className="flex flex-col gap-3">
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
                workTime={index === firstThought ? workTime : null}
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
      </div>
      {(row.status === "cancelled" || row.status === "failed" || finished) && (
        <MessageActions className={FOOTER_CLASS}>
          {finished && copyText && <CopyAction text={copyText} />}
          {showActions && actions.onRegenerate && (
            <MessageAction
              disabled={disabled}
              label="Tạo lại câu trả lời"
              onClick={() => actions.onRegenerate?.(row.id)}
              tooltip="Tạo lại"
            >
              <RefreshCcwIcon />
            </MessageAction>
          )}
          {showActions && (
            <BranchSwitcher
              currentId={row.id}
              disabled={disabled}
              onSwitch={actions.onSwitch}
              siblingIds={row.siblingIds}
            />
          )}
          {finished && <TurnTime createdAt={row.createdAt} />}
          {row.status === "cancelled" && (
            <span className="px-1 text-muted-foreground text-xs">· Đã dừng</span>
          )}
          {row.status === "failed" && (
            <span className="px-1 text-destructive text-xs">Câu trả lời chưa hoàn tất do lỗi</span>
          )}
        </MessageActions>
      )}
    </div>
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
  workTime,
}: {
  turn: Turn;
  messages: readonly AGUIMessage[];
  rowStatus: RowView["status"];
  fileSource?: FileLinkSource;
  isStreaming: boolean;
  workTime?: string | null;
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
      <MessageContent className="w-full text-sm">
        {reasoning && (
          <Reasoning defaultOpen={isReasoningStreaming} isStreaming={isReasoningStreaming}>
            <ReasoningTrigger>
              <ReasoningSummary
                isStreaming={isReasoningStreaming}
                reasoning={reasoning}
                workTime={workTime}
              />
            </ReasoningTrigger>
            <ReasoningContent>{reasoning}</ReasoningContent>
          </Reasoning>
        )}
        {message.content ? (
          <MessageResponse className={ANSWER_CLASS}>{message.content}</MessageResponse>
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
              <Tool className="mb-0 border-border/60">
                <ToolHeader
                  // Steps behind the answer: a regular-weight, muted name.
                  className="[&_span.font-medium]:font-normal [&_span.font-medium]:text-muted-foreground"
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

/** When a turn was saved, shortly; the full time on hover. */
function TurnTime({ createdAt }: { createdAt?: string }) {
  return (
    <time
      className="px-1 text-muted-foreground text-xs"
      dateTime={createdAt}
      title={turnTimeTitle(createdAt)}
    >
      {turnTime(createdAt)}
    </time>
  );
}

/**
 * Puts the chat at its last turn before the first paint; the library alone
 * paints the top first and jumps a frame or two later.
 */
function OpenAtEnd() {
  const { scrollRef } = useStickToBottomContext();
  useLayoutEffect(() => {
    const scroller = scrollRef.current;
    if (scroller) scroller.scrollTop = scroller.scrollHeight;
  }, [scrollRef]);
  return null;
}
