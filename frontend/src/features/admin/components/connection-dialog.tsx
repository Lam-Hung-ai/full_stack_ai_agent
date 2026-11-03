"use client";

import { useId } from "react";
import { Controller, useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
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
import { connectionSchema, type ConnectionValues } from "../schemas/llm.schema";
import type { LlmConnection, LlmProvider } from "../types/llm.types";
import { formatSettings } from "../utils/settings";

/**
 * Create a connection (no `connection`) or edit one. The stored API key is
 * never shown: an empty field keeps it. Mounted only while open.
 */
export function ConnectionDialog({
  connection,
  providers,
  error,
  isPending,
  onClose,
  onSubmit,
}: {
  connection?: LlmConnection;
  providers: readonly LlmProvider[];
  error?: string | null;
  isPending?: boolean;
  onClose: () => void;
  onSubmit: (values: ConnectionValues) => void;
}) {
  const id = useId();
  const form = useForm<ConnectionValues>({
    resolver: zodResolver(connectionSchema),
    defaultValues: {
      key: connection?.key ?? "",
      name: connection?.name ?? "",
      provider: connection?.provider ?? "openrouter",
      clientParams: formatSettings(connection?.client_params ?? {}),
      apiKey: "",
      clearApiKey: false,
      isActive: connection?.is_active ?? true,
    },
  });
  const { errors } = form.formState;
  const clearing = useWatch({ control: form.control, name: "clearApiKey" });

  return (
    <Dialog onOpenChange={(open) => !open && onClose()} open>
      <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-lg">
        <form noValidate onSubmit={form.handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>
              {connection ? `Sửa kết nối ${connection.name}` : "Tạo kết nối"}
            </DialogTitle>
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
                disabled={!!connection}
                id={`${id}-key`}
                placeholder="openrouter"
                {...form.register("key")}
              />
              <FieldError errors={[errors.key]} />
            </Field>
            <Field data-invalid={!!errors.name}>
              <FieldLabel htmlFor={`${id}-name`}>Tên</FieldLabel>
              <Input aria-invalid={!!errors.name} id={`${id}-name`} {...form.register("name")} />
              <FieldError errors={[errors.name]} />
            </Field>
            <Field data-invalid={!!errors.provider}>
              <FieldLabel htmlFor={`${id}-provider`}>Provider (init_chat_model)</FieldLabel>
              <NativeSelect className="w-full" id={`${id}-provider`} {...form.register("provider")}>
                {providers.map((provider) => (
                  <NativeSelectOption
                    disabled={!provider.installed}
                    key={provider.provider}
                    value={provider.provider}
                  >
                    {provider.installed
                      ? provider.provider
                      : `${provider.provider} (chưa cài ${provider.package})`}
                  </NativeSelectOption>
                ))}
              </NativeSelect>
              <FieldError errors={[errors.provider]} />
            </Field>
            <Field data-invalid={!!errors.apiKey}>
              <FieldLabel htmlFor={`${id}-api-key`}>API key</FieldLabel>
              <Input
                autoComplete="off"
                disabled={clearing}
                id={`${id}-api-key`}
                placeholder={
                  connection?.has_api_key ? `Đã lưu …${connection.api_key_hint}` : "Không có"
                }
                type="password"
                {...form.register("apiKey")}
              />
              <FieldDescription>
                Lưu mã hoá, không hiện lại. {connection?.has_api_key && "Để trống để giữ key cũ."}
              </FieldDescription>
            </Field>
            {connection?.has_api_key && (
              <Controller
                control={form.control}
                name="clearApiKey"
                render={({ field }) => (
                  <Field orientation="horizontal">
                    <Checkbox
                      checked={field.value}
                      id={`${id}-clear`}
                      onCheckedChange={(value) => field.onChange(value === true)}
                    />
                    <FieldLabel className="font-normal" htmlFor={`${id}-clear`}>
                      Xoá API key đã lưu
                    </FieldLabel>
                  </Field>
                )}
              />
            )}
            <Field data-invalid={!!errors.clientParams}>
              <FieldLabel htmlFor={`${id}-params`}>Tham số client (JSON)</FieldLabel>
              <Textarea
                aria-invalid={!!errors.clientParams}
                className="font-mono text-xs"
                id={`${id}-params`}
                placeholder={'{"openrouter_api_base": "https://openrouter.ai/api/v1"}'}
                rows={4}
                {...form.register("clientParams")}
              />
              <FieldDescription>
                Truyền nguyên vào init_chat_model; không đặt key ở đây.
              </FieldDescription>
              <FieldError errors={[errors.clientParams]} />
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
