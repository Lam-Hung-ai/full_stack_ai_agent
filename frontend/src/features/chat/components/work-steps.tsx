"use client";

import { useState } from "react";
import {
  BrainIcon,
  ClockIcon,
  FilePlusIcon,
  ListChecksIcon,
  type LucideIcon,
  MessageSquareTextIcon,
  TriangleAlertIcon,
  WrenchIcon,
} from "lucide-react";
import { CodeBlock } from "@/components/ai-elements/code-block";
import { MessageResponse } from "@/components/ai-elements/message";
import {
  Trace,
  TraceCollapsible,
  TraceCollapsibleContent,
  TraceCollapsibleTrigger,
  TraceDescription,
  TraceIcon,
  TraceLine,
  TraceTitle,
} from "@/components/ui/trace";
import { cn } from "@/lib/utils";
import type { RowView } from "../types/chat.types";
import { parseToolArgs } from "../utils/agui-messages";
import type { WorkStep } from "../utils/answer-blocks";
import { type AttachedFile, madeFile } from "../utils/files";
import { type FileLinkSource, MessageFiles } from "./message-files";

type ToolStep = Extract<WorkStep, { kind: "tool" }>;

/** Thinking and notes: small and compact, a step behind the answer. */
const NOTE_CLASS = cn(
  "text-[13px] leading-relaxed",
  "[&>*]:my-1.5 [&_:is(ul,ol)]:my-1 [&_li]:my-0.5 [&_:is(h1,h2,h3,h4)]:text-[13px]",
);

/** How a known tool reads in the trace; others show their name. */
const TOOLS: Record<
  string,
  { icon: LucideIcon; label: (args: Record<string, unknown>) => string }
> = {
  get_current_time: { icon: ClockIcon, label: () => "Xem giờ hiện tại" },
  create_file: {
    icon: FilePlusIcon,
    label: (args) => (typeof args.name === "string" ? `Tạo tệp ${args.name}` : "Tạo tệp"),
  },
};

type ToolStatus = "done" | "running" | "error" | "pending" | "stopped";

const STATUS_TEXT: Partial<Record<ToolStatus, string>> = {
  running: "Đang chạy…",
  error: "Lỗi",
  pending: "Chờ duyệt",
  stopped: "Đã dừng",
};

function toolStatus(step: ToolStep, rowStatus: RowView["status"], active: boolean): ToolStatus {
  if (step.result) return step.result.error ? "error" : "done";
  if (active) return "running";
  if (rowStatus === "requires_action") return "pending";
  if (rowStatus === "failed") return "error";
  if (rowStatus === "cancelled") return "stopped";
  return "running";
}

function argsOf(step: ToolStep): Record<string, unknown> {
  const args = parseToolArgs(step.call.function.arguments);
  return args && typeof args === "object" ? (args as Record<string, unknown>) : {};
}

/** Shown before the first step arrives; `label` counts the seconds. */
export function WorkingLine({ label }: { label: string }) {
  return (
    <TraceLine status="running">
      <TraceIcon>
        <ListChecksIcon />
      </TraceIcon>
      <TraceTitle>{label}</TraceTitle>
    </TraceLine>
  );
}

/** What the last step is doing, for the header while the run goes on. */
function currentStep(step: WorkStep | undefined): string | null {
  if (step?.kind === "thinking") return "đang suy nghĩ";
  if (step?.kind !== "tool") return null;
  const known = TOOLS[step.call.function.name];
  return `đang chạy ${known ? known.label(argsOf(step)) : step.call.function.name}`;
}

/**
 * A run of the agent's work as a trace, like Kimi: thinking, notes and tool
 * calls on a line under one header. It stays open while the answer is being
 * written (`keepOpen`) and folds once it is done, unless a step failed;
 * whatever the reader chose wins. Files a tool made stay visible below.
 */
export function WorkSteps({
  steps,
  summary,
  running,
  keepOpen,
  rowStatus,
  fileSource,
}: {
  steps: readonly WorkStep[];
  summary: string;
  /** This run is the one going on now. */
  running: boolean;
  keepOpen: boolean;
  rowStatus: RowView["status"];
  fileSource?: FileLinkSource;
}) {
  const [choice, setChoice] = useState<boolean | null>(null);
  // A failed step must not hide in a folded trace (Norman's "dr" mode).
  const failed = steps.filter(
    (step) => step.kind === "tool" && toolStatus(step, rowStatus, running) === "error",
  ).length;
  const open = choice ?? (keepOpen || failed > 0);
  const now = running ? currentStep(steps.at(-1)) : null;
  const files = steps.flatMap((step): AttachedFile[] => {
    if (step.kind !== "tool") return [];
    const made = madeFile(step.call.function.name, step.result?.content);
    return made ? [made] : [];
  });

  return (
    <div className="flex flex-col gap-2">
      <TraceCollapsible onOpenChange={setChoice} open={open}>
        <TraceCollapsibleTrigger>
          <TraceLine status={running ? "running" : undefined}>
            <TraceIcon>
              {failed > 0 && !running ? (
                <TriangleAlertIcon className="text-destructive" />
              ) : (
                <ListChecksIcon />
              )}
            </TraceIcon>
            <TraceTitle>{summary}</TraceTitle>
            <TraceDescription>· {now ?? `${steps.length} bước`}</TraceDescription>
            {failed > 0 && (
              <TraceDescription className="text-destructive">· {failed} bước lỗi</TraceDescription>
            )}
          </TraceLine>
        </TraceCollapsibleTrigger>
        <TraceCollapsibleContent className="border-dashed text-sm">
          <Trace className="gap-3">
            {steps.map((step, index) => (
              <Step
                active={running && index === steps.length - 1}
                key={step.id}
                rowStatus={rowStatus}
                step={step}
              />
            ))}
          </Trace>
        </TraceCollapsibleContent>
      </TraceCollapsible>
      {fileSource && files.length > 0 && (
        <MessageFiles align="start" files={files} source={fileSource} />
      )}
    </div>
  );
}

function Step({
  step,
  active,
  rowStatus,
}: {
  step: WorkStep;
  active: boolean;
  rowStatus: RowView["status"];
}) {
  if (step.kind === "note") {
    return (
      <div className="flex gap-2 text-muted-foreground">
        <TraceIcon className="mt-1">
          <MessageSquareTextIcon />
        </TraceIcon>
        <MessageResponse className={cn(NOTE_CLASS, "min-w-0 flex-1")}>{step.text}</MessageResponse>
      </div>
    );
  }

  if (step.kind === "thinking") {
    return (
      // Open: the trace itself is folded once the answer is done.
      <TraceCollapsible defaultOpen>
        <TraceCollapsibleTrigger>
          <TraceLine status={active ? "running" : undefined}>
            <TraceIcon>
              <BrainIcon />
            </TraceIcon>
            <TraceTitle>{active ? "Đang suy nghĩ…" : "Đã suy nghĩ"}</TraceTitle>
          </TraceLine>
        </TraceCollapsibleTrigger>
        <TraceCollapsibleContent className="border-dashed">
          <MessageResponse className={NOTE_CLASS}>{step.text}</MessageResponse>
        </TraceCollapsibleContent>
      </TraceCollapsible>
    );
  }

  const args = argsOf(step);
  const known = TOOLS[step.call.function.name];
  const Icon = known?.icon ?? WrenchIcon;
  const status = toolStatus(step, rowStatus, active);
  const lineStatus = status === "done" || status === "stopped" ? undefined : status;
  return (
    <TraceCollapsible>
      <TraceCollapsibleTrigger>
        <TraceLine status={lineStatus}>
          <TraceIcon>
            <Icon />
          </TraceIcon>
          <TraceTitle>{known ? known.label(args) : step.call.function.name}</TraceTitle>
          {STATUS_TEXT[status] && <TraceDescription>· {STATUS_TEXT[status]}</TraceDescription>}
        </TraceLine>
      </TraceCollapsibleTrigger>
      <TraceCollapsibleContent className="flex flex-col gap-3 border-dashed">
        <ToolPart code={JSON.stringify(args, null, 2)} title="Đầu vào" />
        {step.result && (
          <ToolPart
            code={step.result.error ?? textOf(step.result.content)}
            isError={!!step.result.error}
            title={step.result.error ? "Lỗi" : "Kết quả"}
          />
        )}
      </TraceCollapsibleContent>
    </TraceCollapsible>
  );
}

/** A tool result as text: a string as is, content parts as JSON. */
function textOf(content: unknown): string {
  return typeof content === "string" ? content : JSON.stringify(content, null, 2);
}

function ToolPart({ title, code, isError }: { title: string; code: string; isError?: boolean }) {
  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <span className={isError ? "text-destructive text-xs" : "text-xs"}>{title}</span>
      <CodeBlock className="text-xs" code={code} language="json" />
    </div>
  );
}
