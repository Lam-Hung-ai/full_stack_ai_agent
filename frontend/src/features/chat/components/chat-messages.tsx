"use client";

import { useLayoutEffect, useState } from "react";
import { useStickToBottomContext } from "use-stick-to-bottom";
import { PencilIcon, RefreshCcwIcon, RotateCcwIcon } from "lucide-react";
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  Message,
  MessageAction,
  MessageActions,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
import { useElapsedSeconds } from "@/hooks/use-elapsed-seconds";
import { cn } from "@/lib/utils";
import type { RowView } from "../types/chat.types";
import { answerBlocks, answerCopyText, workSummary } from "../utils/answer-blocks";
import { isActive, isTerminal } from "../utils/history";
import { attachedFiles, questionText as textOf } from "../utils/files";
import { formatDuration, turnTime, turnTimeTitle, workDuration } from "../utils/turn-time";
import { type InteractionAnswer, interactionOf } from "../utils/interactions";
import { BranchSwitcher } from "./branch-switcher";
import { CopyAction } from "./copy-action";
import { EditQuestionForm } from "./edit-question-form";
import { InteractionCard } from "./interaction-card";
import { type FileLinkSource, MessageFiles } from "./message-files";
import { WorkingLine, WorkSteps } from "./work-steps";

/**
 * Answer prose: 16px serif with relaxed leading, filling the 768px column
 * like every other block (about 95 characters a line); assistant messages
 * drop the library's 95% cap so all blocks share the column's edges.
 * Headings sit tighter.
 */
const ANSWER_CLASS = cn(
  "font-serif text-base leading-relaxed",
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
  const blocks = answerBlocks(row.content);
  // Content is saved when a turn ends: one running elsewhere has none yet.
  const waiting = isStreaming || (!row.live && isActive(row));
  const finished = !row.live && isTerminal(row);
  const showActions = actions && finished;
  const copyText = answerCopyText(blocks);
  // Like ChatGPT's "Worked for 7s", on the answer's first run of work.
  // Runs summed by the backend; older rows fall back to their whole span.
  const workTime = !finished
    ? null
    : row.workSeconds != null
      ? formatDuration(row.workSeconds)
      : workDuration(row.createdAt, row.updatedAt);
  const firstWork = blocks.findIndex((block) => block.kind === "work");
  const lastWork = blocks.findLastIndex((block) => block.kind === "work");
  // Feedback while waiting: the seconds this tab has watched it work.
  const elapsed = useElapsedSeconds(isStreaming);
  const stoppedOrFailed = finished && (row.status === "cancelled" || row.status === "failed");
  const rowStatus = row.live ? "running" : row.status;
  // Only a saved pause can be answered; the server checks it again.
  const onAnswer =
    answerable && !row.live && row.status === "requires_action" ? actions?.onAnswer : undefined;

  return (
    // One block, so the footer sits right under the answer instead of a
    // whole conversation gap below it.
    <div className="flex flex-col gap-2">
      {/* Blocks of one answer sit closer than turns do (32px). */}
      <div className="flex flex-col gap-3">
        {blocks.length === 0 && waiting && (
          <WorkingLine
            label={workSummary({
              running: true,
              elapsed,
              status: row.status,
              workTime: null,
              isFirst: true,
              isLast: true,
            })}
          />
        )}
        {blocks.map((block, index) => {
          if (block.kind === "work") {
            const running = isStreaming && index === blocks.length - 1;
            return (
              <WorkSteps
                fileSource={fileSource}
                // Open until the whole answer is written, so a step being
                // read does not fold away when the text starts; a stopped
                // or failed row keeps its last run open.
                keepOpen={isStreaming || (stoppedOrFailed && index === lastWork)}
                key={block.id}
                rowStatus={rowStatus}
                running={running}
                steps={block.steps}
                summary={workSummary({
                  running,
                  elapsed,
                  status: row.status,
                  workTime,
                  isFirst: index === firstWork,
                  isLast: index === lastWork,
                })}
              />
            );
          }
          if (block.kind === "text") {
            return (
              <Message className="max-w-full" from="assistant" key={block.id}>
                <MessageContent className="w-full text-sm">
                  <MessageResponse className={ANSWER_CLASS}>{block.text}</MessageResponse>
                </MessageContent>
              </Message>
            );
          }
          const interaction = interactionOf(block.message);
          if (!interaction) return null;
          return (
            <Message className="max-w-full" from="assistant" key={block.message.id}>
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
