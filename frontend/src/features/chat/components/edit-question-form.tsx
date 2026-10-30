"use client";

import { useId } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";
import { questionSchema, type QuestionValues } from "../schemas/chat.schema";

/** Inline editor for a question; saving asks it as a new version. */
export function EditQuestionForm({
  defaultText,
  onCancel,
  onSubmit,
}: {
  defaultText: string;
  onCancel: () => void;
  onSubmit: (text: string) => void;
}) {
  const id = useId();
  const form = useForm<QuestionValues>({
    resolver: zodResolver(questionSchema),
    defaultValues: { text: defaultText },
  });
  const { errors } = form.formState;

  return (
    <form
      className="flex w-full max-w-[80%] flex-col gap-2 self-end"
      noValidate
      onSubmit={form.handleSubmit((values) => onSubmit(values.text))}
    >
      <Field data-invalid={!!errors.text}>
        <FieldLabel className="sr-only" htmlFor={`${id}-text`}>
          Sửa câu hỏi
        </FieldLabel>
        <Textarea
          autoFocus
          aria-invalid={!!errors.text}
          id={`${id}-text`}
          {...form.register("text")}
        />
        <FieldError errors={[errors.text]} />
      </Field>
      <div className="flex justify-end gap-2">
        <Button onClick={onCancel} size="sm" type="button" variant="ghost">
          Huỷ
        </Button>
        <Button size="sm" type="submit">
          Gửi
        </Button>
      </div>
    </form>
  );
}
