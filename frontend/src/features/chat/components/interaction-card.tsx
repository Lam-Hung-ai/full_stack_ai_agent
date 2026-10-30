"use client";

import { useId } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { CheckIcon, MessageCircleQuestionIcon, ShieldQuestionIcon, XIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";
import { answerSchema, type AnswerValues } from "../schemas/chat.schema";
import type { Interaction, InteractionAnswer } from "../utils/interactions";

/**
 * A question the agent asks, or a tool it wants to run, inside its answer.
 * `onAnswer` is given only while this tab can answer it.
 */
export function InteractionCard({
  interaction,
  draft,
  onAnswer,
}: {
  interaction: Interaction;
  draft?: InteractionAnswer;
  onAnswer?: (answer: InteractionAnswer) => void;
}) {
  const waiting = interaction.status === "waiting" && !draft;
  return (
    <div className="flex flex-col gap-2 rounded-lg border bg-muted/40 p-3 text-sm">
      {interaction.kind === "tool_approval" ? (
        <ApprovalBody interaction={interaction} />
      ) : (
        <p className="flex items-start gap-2 font-medium">
          <MessageCircleQuestionIcon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
          {interaction.question}
        </p>
      )}
      {waiting && onAnswer ? (
        interaction.kind === "tool_approval" ? (
          <div className="flex gap-2">
            <Button onClick={() => onAnswer({ approved: true })} size="sm">
              <CheckIcon />
              Cho phép
            </Button>
            <Button onClick={() => onAnswer({ approved: false })} size="sm" variant="outline">
              <XIcon />
              Từ chối
            </Button>
          </div>
        ) : (
          <AnswerForm onAnswer={onAnswer} />
        )
      ) : (
        <Outcome draft={draft} interaction={interaction} />
      )}
    </div>
  );
}

function ApprovalBody({ interaction }: { interaction: Interaction }) {
  const args = JSON.stringify(interaction.arguments ?? {}, null, 2);
  return (
    <>
      <p className="flex items-start gap-2 font-medium">
        <ShieldQuestionIcon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
        Agent muốn dùng công cụ <code className="font-mono">{interaction.tool_name}</code>
      </p>
      {args !== "{}" && (
        <pre className="overflow-x-auto rounded-md bg-background p-2 font-mono text-xs">{args}</pre>
      )}
    </>
  );
}

function Outcome({ interaction, draft }: { interaction: Interaction; draft?: InteractionAnswer }) {
  if (draft) return <p className="text-muted-foreground">Đã ghi nhận, đang chờ các câu trả lời còn lại.</p>;
  if (interaction.status === "cancelled") return <p className="text-muted-foreground">Đã huỷ.</p>;
  if (interaction.status === "waiting") {
    return <p className="text-muted-foreground">Đang chờ người dùng trả lời.</p>;
  }
  if (interaction.kind === "tool_approval") {
    const approved = (interaction.response as { approved?: boolean } | undefined)?.approved;
    return <p className="text-muted-foreground">{approved ? "Đã cho phép." : "Đã từ chối."}</p>;
  }
  return (
    <p>
      <span className="text-muted-foreground">Bạn trả lời: </span>
      {String(interaction.response ?? "")}
    </p>
  );
}

function AnswerForm({ onAnswer }: { onAnswer: (answer: InteractionAnswer) => void }) {
  const id = useId();
  const form = useForm<AnswerValues>({
    resolver: zodResolver(answerSchema),
    defaultValues: { answer: "" },
  });
  const { errors } = form.formState;
  return (
    <form
      className="flex flex-col gap-2"
      noValidate
      onSubmit={form.handleSubmit((values) => onAnswer({ answer: values.answer }))}
    >
      <Field data-invalid={!!errors.answer}>
        <FieldLabel className="sr-only" htmlFor={`${id}-answer`}>
          Câu trả lời
        </FieldLabel>
        <Textarea
          aria-invalid={!!errors.answer}
          id={`${id}-answer`}
          placeholder="Nhập câu trả lời…"
          {...form.register("answer")}
        />
        <FieldError errors={[errors.answer]} />
      </Field>
      <Button className="self-end" size="sm" type="submit">
        Gửi trả lời
      </Button>
    </form>
  );
}
