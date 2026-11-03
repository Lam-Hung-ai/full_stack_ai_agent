"use client";

import { useId } from "react";
import { Controller, useForm } from "react-hook-form";
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
import { Field, FieldError, FieldGroup, FieldLabel, FieldLegend, FieldSet } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import type { Permission, Role } from "../types/organization.types";
import { roleSchema, type RoleValues } from "../schemas/organization.schema";
import { groupPermissions, roleLabel } from "../utils/permissions";

/**
 * Create a role (no `role`) or edit one. Built-in roles keep their name;
 * permissions the editor lacks are shown but cannot be added (the API
 * refuses them too). Mounted only while open.
 */
export function RoleDialog({
  role,
  catalog,
  grantable,
  error,
  isPending,
  onClose,
  onSubmit,
}: {
  role?: Role;
  catalog: readonly Permission[];
  /** What the editor may hand out; null means everything (an owner). */
  grantable: ReadonlySet<string> | null;
  error?: string | null;
  isPending?: boolean;
  onClose: () => void;
  onSubmit: (values: RoleValues) => void;
}) {
  const id = useId();
  const builtIn = !!role?.role_key;
  const form = useForm<RoleValues>({
    resolver: zodResolver(roleSchema),
    defaultValues: {
      name: role ? roleLabel(role) : "",
      description: role?.description ?? "",
      permissions: role?.permissions ?? [],
    },
  });
  const { errors } = form.formState;
  const initial = new Set(role?.permissions ?? []);

  return (
    <Dialog onOpenChange={(open) => !open && onClose()} open>
      <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-lg">
        <form noValidate onSubmit={form.handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>{role ? `Sửa vai trò ${roleLabel(role)}` : "Tạo vai trò"}</DialogTitle>
          </DialogHeader>
          <FieldGroup className="py-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <Field data-invalid={!!errors.name}>
              <FieldLabel htmlFor={`${id}-name`}>Tên vai trò</FieldLabel>
              <Input
                aria-invalid={!!errors.name}
                disabled={builtIn}
                id={`${id}-name`}
                {...form.register("name")}
              />
              <FieldError errors={[errors.name]} />
            </Field>
            <Field data-invalid={!!errors.description}>
              <FieldLabel htmlFor={`${id}-description`}>Mô tả</FieldLabel>
              <Input
                aria-invalid={!!errors.description}
                disabled={builtIn}
                id={`${id}-description`}
                {...form.register("description")}
              />
              <FieldError errors={[errors.description]} />
            </Field>
            <Controller
              control={form.control}
              name="permissions"
              render={({ field }) => (
                <>
                  {groupPermissions(catalog).map((group) => (
                    <FieldSet key={group.resource}>
                      <FieldLegend variant="label">{group.label}</FieldLegend>
                      {group.permissions.map((permission) => {
                        const checked = field.value.includes(permission.key);
                        // Keeping a grant is always allowed; adding needs holding it.
                        const locked =
                          !checked && !initial.has(permission.key) && grantable !== null
                            ? !grantable.has(permission.key)
                            : false;
                        return (
                          <Field key={permission.key} orientation="horizontal">
                            <Checkbox
                              checked={checked}
                              disabled={locked}
                              id={`${id}-${permission.key}`}
                              onCheckedChange={(value) =>
                                field.onChange(
                                  value === true
                                    ? [...field.value, permission.key]
                                    : field.value.filter((key) => key !== permission.key),
                                )
                              }
                            />
                            <FieldLabel
                              className="font-normal"
                              htmlFor={`${id}-${permission.key}`}
                            >
                              {permission.description ?? permission.key}
                            </FieldLabel>
                          </Field>
                        );
                      })}
                    </FieldSet>
                  ))}
                </>
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
