"use client";

import { useState } from "react";
import { FlaskConicalIcon, PencilIcon, PlusIcon, Trash2Icon } from "lucide-react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useConnections, useLlmActions, useModels } from "../hooks/use-llm";
import type { ModelValues } from "../schemas/llm.schema";
import type { LlmModel } from "../types/llm.types";
import { llmErrorMessage } from "../utils/error-message";
import { parseSettings } from "../utils/settings";
import { ModelDialog } from "./model-dialog";

type Editing = { mode: "create" } | { mode: "edit"; model: LlmModel };

export function ModelsPanel() {
  const models = useModels();
  const connections = useConnections();
  const actions = useLlmActions();
  const [editing, setEditing] = useState<Editing | null>(null);
  const [deleting, setDeleting] = useState<LlmModel | null>(null);
  const save = editing?.mode === "edit" ? actions.updateModel : actions.createModel;

  const submit = (values: ModelValues) => {
    const onSuccess = () => setEditing(null);
    const input = {
      connection_id: values.connectionId,
      model: values.model,
      name: values.name,
      params: parseSettings(values.params) ?? {},
      is_active: values.isActive,
    };
    if (editing?.mode === "edit") {
      actions.updateModel.mutate({ id: editing.model.id, input }, { onSuccess });
    } else {
      actions.createModel.mutate({ ...input, key: values.key }, { onSuccess });
    }
  };

  const test = (model: LlmModel) =>
    actions.testModel.mutate(model.id, {
      onSuccess: (result) =>
        result.ok
          ? toast.success(`${model.name} trả lời: ${result.detail}`)
          : toast.error(`${model.name} lỗi: ${result.detail}`),
      onError: (error) => toast.error(llmErrorMessage(error)),
    });

  if (models.isPending || connections.isPending) return <Spinner aria-label="Đang tải model" />;
  if (models.isError || connections.isError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{llmErrorMessage(models.error ?? connections.error)}</AlertDescription>
      </Alert>
    );
  }

  const connectionName = new Map(connections.data.data.map((c) => [c.id, c.name]));
  const testing = actions.testModel.isPending ? actions.testModel.variables : null;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex justify-end">
        <Button
          disabled={connections.data.data.length === 0}
          onClick={() => setEditing({ mode: "create" })}
          size="sm"
        >
          <PlusIcon />
          Tạo model
        </Button>
      </div>
      {actions.deleteModel.isError && (
        <Alert variant="destructive">
          <AlertDescription>{llmErrorMessage(actions.deleteModel.error)}</AlertDescription>
        </Alert>
      )}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Model</TableHead>
            <TableHead>Tên phía provider</TableHead>
            <TableHead>Kết nối</TableHead>
            <TableHead className="w-32" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {models.data.data.length === 0 && (
            <TableRow>
              <TableCell className="text-muted-foreground" colSpan={4}>
                {connections.data.data.length === 0
                  ? "Tạo một kết nối trước khi thêm model."
                  : "Chưa có model."}
              </TableCell>
            </TableRow>
          )}
          {models.data.data.map((model) => (
            <TableRow key={model.id}>
              <TableCell>
                <div className="flex items-center gap-2 font-medium">
                  {model.name}
                  {!model.is_active && <Badge variant="secondary">Tắt</Badge>}
                </div>
                <div className="text-muted-foreground text-xs">{model.key}</div>
              </TableCell>
              <TableCell className="font-mono text-xs">{model.model}</TableCell>
              <TableCell>{connectionName.get(model.connection_id) ?? "—"}</TableCell>
              <TableCell>
                <div className="flex justify-end gap-1">
                  <Button
                    aria-label={`Thử model ${model.name}`}
                    disabled={testing === model.id}
                    onClick={() => test(model)}
                    size="icon"
                    variant="ghost"
                  >
                    {testing === model.id ? <Spinner /> : <FlaskConicalIcon />}
                  </Button>
                  <Button
                    aria-label={`Sửa model ${model.name}`}
                    onClick={() => setEditing({ mode: "edit", model })}
                    size="icon"
                    variant="ghost"
                  >
                    <PencilIcon />
                  </Button>
                  <Button
                    aria-label={`Xoá model ${model.name}`}
                    onClick={() => setDeleting(model)}
                    size="icon"
                    variant="ghost"
                  >
                    <Trash2Icon />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {editing && (
        <ModelDialog
          connections={connections.data.data}
          error={save.isError ? llmErrorMessage(save.error) : null}
          isPending={save.isPending}
          model={editing.mode === "edit" ? editing.model : undefined}
          onClose={() => {
            save.reset();
            setEditing(null);
          }}
          onSubmit={submit}
        />
      )}
      {deleting && (
        <ConfirmDialog
          description={`Model ${deleting.name} sẽ bị xoá.`}
          onClose={() => setDeleting(null)}
          onConfirm={() => {
            actions.deleteModel.mutate(deleting.id);
            setDeleting(null);
          }}
          title="Xoá model?"
        />
      )}
    </div>
  );
}
