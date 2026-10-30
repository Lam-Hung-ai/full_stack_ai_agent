"use client";

import { useId } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";

// Mirrors the backend `Name` (1–200 characters); FastAPI stays the authority.
const nameSchema = z.object({
  name: z.string().trim().min(1, "Nhập tên").max(200, "Tên quá dài"),
});

type NameValues = z.infer<typeof nameSchema>;

/**
 * Asks for one name (a chat, a folder, an organization). Mounted only while
 * open, so each opening starts from `defaultName`.
 */
export function NameDialog({
  title,
  label,
  defaultName = "",
  submitLabel = "Lưu",
  error,
  isPending,
  onClose,
  onSubmit,
}: {
  title: string;
  label: string;
  defaultName?: string;
  submitLabel?: string;
  error?: string | null;
  isPending?: boolean;
  onClose: () => void;
  onSubmit: (name: string) => void;
}) {
  const id = useId();
  const form = useForm<NameValues>({
    resolver: zodResolver(nameSchema),
    defaultValues: { name: defaultName },
  });
  const { errors } = form.formState;

  return (
    <Dialog onOpenChange={(open) => !open && onClose()} open>
      <DialogContent className="sm:max-w-sm">
        <form noValidate onSubmit={form.handleSubmit((values) => onSubmit(values.name))}>
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-3 py-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <Field data-invalid={!!errors.name}>
              <FieldLabel htmlFor={`${id}-name`}>{label}</FieldLabel>
              <Input
                autoFocus
                aria-invalid={!!errors.name}
                id={`${id}-name`}
                {...form.register("name")}
              />
              <FieldError errors={[errors.name]} />
            </Field>
          </div>
          <DialogFooter>
            <Button onClick={onClose} type="button" variant="ghost">
              Huỷ
            </Button>
            <Button disabled={isPending} type="submit">
              {submitLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
