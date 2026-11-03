"use client";

import { useId } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useSelectWorkspace } from "@/features/workspaces";
import { useCreateOrganization } from "../hooks/use-organization";
import { organizationErrorMessage } from "../utils/error-message";

const schema = z.object({ name: z.string().trim().min(1, "Nhập tên tổ chức").max(200) });

export function CreateOrganizationScreen() {
  const id = useId();
  const router = useRouter();
  const selectWorkspace = useSelectWorkspace();
  const createMutation = useCreateOrganization();
  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { name: "" },
  });
  const { errors } = form.formState;

  const onSubmit = form.handleSubmit((values) =>
    createMutation.mutate(values.name, {
      onSuccess: (organization) => {
        // Work in the new organization from now on.
        selectWorkspace(organization.workspace_id);
        router.push(`/organizations/${organization.id}`);
      },
    }),
  );

  return (
    <div className="flex h-full items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Tạo tổ chức</CardTitle>
          <CardDescription>
            Bạn là chủ sở hữu và có thể mời thành viên ngay sau khi tạo.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form noValidate onSubmit={onSubmit}>
            <FieldGroup>
              {createMutation.isError && (
                <Alert variant="destructive">
                  <AlertDescription>
                    {organizationErrorMessage(createMutation.error)}
                  </AlertDescription>
                </Alert>
              )}
              <Field data-invalid={!!errors.name}>
                <FieldLabel htmlFor={`${id}-name`}>Tên tổ chức</FieldLabel>
                <Input
                  autoFocus
                  aria-invalid={!!errors.name}
                  id={`${id}-name`}
                  {...form.register("name")}
                />
                <FieldError errors={[errors.name]} />
              </Field>
              <Button disabled={createMutation.isPending} type="submit">
                {createMutation.isPending ? "Đang tạo…" : "Tạo tổ chức"}
              </Button>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
