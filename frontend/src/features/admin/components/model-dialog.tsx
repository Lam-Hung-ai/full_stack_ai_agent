"use client";

import { useId } from "react";
import { Controller, useForm } from "react-hook-form";
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
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { modelSchema, type ModelValues } from "../schemas/llm.schema";
import type { LlmConnection, LlmModel } from "../types/llm.types";
import { formatSettings } from "../utils/settings";

/** Create a model (no `model`) or edit one. Mounted only while open. */
export function ModelDialog({
  model,
  connections,
  error,
  isPending,
  onClose,
  onSubmit,
}: {
  model?: LlmModel;
  connections: readonly LlmConnection[];
  error?: string | null;
  isPending?: boolean;
  onClose: () => void;
  onSubmit: (values: ModelValues) => void;
}) {
  const id = useId();
  const form = useForm<ModelValues>({
    resolver: zodResolver(modelSchema),
    defaultValues: {
      key: model?.key ?? "",
      name: model?.name ?? "",
      connectionId: model?.connection_id ?? connections[0]?.id ?? "",
      model: model?.model ?? "",
      params: formatSettings(model?.params ?? {}),
      isActive: model?.is_active ?? true,
    },
  });
  const { errors } = form.formState;

  return (
    <Dialog onOpenChange={(open) => !open && onClose()} open>
      <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-lg">
        <form noValidate onSubmit={form.handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>{model ? `Sửa model ${model.name}` : "Tạo model"}</DialogTitle>
          </DialogHeader>
          <FieldGroup className="py-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <Field data-invalid={!!errors.key}>
              <FieldLabel htmlFor={`${id}-key`}>Mã</FieldLabel>
              <Input
                aria-invalid={!!errors.key}
                disabled={!!model}
                id={`${id}-key`}
                placeholder="claude-sonnet"
                {...form.register("key")}
              />
              <FieldError errors={[errors.key]} />
            </Field>
            <Field data-invalid={!!errors.name}>
              <FieldLabel htmlFor={`${id}-name`}>Tên hiển thị</FieldLabel>
              <Input aria-invalid={!!errors.name} id={`${id}-name`} {...form.register("name")} />
              <FieldError errors={[errors.name]} />
            </Field>
            <Field data-invalid={!!errors.connectionId}>
              <FieldLabel htmlFor={`${id}-connection`}>Kết nối</FieldLabel>
              <NativeSelect
                aria-invalid={!!errors.connectionId}
                className="w-full"
                id={`${id}-connection`}
                {...form.register("connectionId")}
              >
                {connections.map((connection) => (
                  <NativeSelectOption key={connection.id} value={connection.id}>
                    {connection.name} ({connection.provider})
                  </NativeSelectOption>
                ))}
              </NativeSelect>
              <FieldError errors={[errors.connectionId]} />
            </Field>
            <Field data-invalid={!!errors.model}>
              <FieldLabel htmlFor={`${id}-model`}>Tên model của provider</FieldLabel>
              <Input
                aria-invalid={!!errors.model}
                id={`${id}-model`}
                placeholder="anthropic/claude-sonnet-4.5"
                {...form.register("model")}
              />
              <FieldError errors={[errors.model]} />
            </Field>
            <Field data-invalid={!!errors.params}>
              <FieldLabel htmlFor={`${id}-params`}>Tham số model (JSON)</FieldLabel>
              <Textarea
                aria-invalid={!!errors.params}
                className="font-mono text-xs"
                id={`${id}-params`}
                placeholder={'{"reasoning": {"effort": "high"}, "temperature": 0.2}'}
                rows={4}
                {...form.register("params")}
              />
              <FieldDescription>Truyền nguyên vào init_chat_model.</FieldDescription>
              <FieldError errors={[errors.params]} />
            </Field>
            <Controller
              control={form.control}
              name="isActive"
              render={({ field }) => (
                <Field orientation="horizontal">
                  <Switch
                    checked={field.value}
                    id={`${id}-active`}
                    onCheckedChange={field.onChange}
                  />
                  <FieldLabel className="font-normal" htmlFor={`${id}-active`}>
                    Đang dùng
                  </FieldLabel>
                </Field>
              )}
            />
          </FieldGroup>
          <DialogFooter>
            <Button onClick={onClose} type="button" variant="ghost">
              Huỷ
            </Button>
            <Button disabled={isPending} type="submit">
              Lưu
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
