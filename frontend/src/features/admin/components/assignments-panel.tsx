"use client";

import { useState } from "react";
import { ArrowDownIcon, ArrowUpIcon, XIcon } from "lucide-react";
import { toast } from "sonner";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { Spinner } from "@/components/ui/spinner";
import { useAssignments, useLlmActions, useModels } from "../hooks/use-llm";
import type { LlmAssignment, LlmModel } from "../types/llm.types";
import { addModel, moveModel, removeModel } from "../utils/assignment";
import { llmErrorMessage } from "../utils/error-message";

export function AssignmentsPanel() {
  const assignments = useAssignments();
  const models = useModels();

  if (assignments.isPending || models.isPending) return <Spinner aria-label="Đang tải phân công" />;
  if (assignments.isError || models.isError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{llmErrorMessage(assignments.error ?? models.error)}</AlertDescription>
      </Alert>
    );
  }
  return (
    <div className="flex flex-col gap-3">
      {assignments.data.data.map((assignment) => (
        // Keyed by the saved list so a save (or another admin's) resets the draft.
        <PurposeCard
          assignment={assignment}
          key={`${assignment.purpose}:${assignment.model_ids.join(",")}`}
          models={models.data.data}
        />
      ))}
    </div>
  );
}

function PurposeCard({
  assignment,
  models,
}: {
  assignment: LlmAssignment;
  models: readonly LlmModel[];
}) {
  const actions = useLlmActions();
  const [ids, setIds] = useState<string[]>(assignment.model_ids);
  const byId = new Map(models.map((model) => [model.id, model]));
  const addable = models.filter((model) => model.is_active && !ids.includes(model.id));
  const changed = ids.join(",") !== assignment.model_ids.join(",");

  const save = () =>
    actions.setAssignment.mutate(
      { purpose: assignment.purpose, modelIds: ids },
      {
        onSuccess: () => toast.success(`Đã lưu model cho “${assignment.description}”.`),
        onError: (error) => toast.error(llmErrorMessage(error)),
      },
    );

  return (
    <Card>
      <CardHeader>
        <CardTitle>{assignment.description}</CardTitle>
        <CardDescription>
          Model đầu trả lời, các model sau dùng dự phòng khi model trước lỗi. Để trống thì dùng cấu
          hình biến môi trường.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        {ids.length === 0 && (
          <p className="text-muted-foreground text-sm">Đang dùng cấu hình biến môi trường.</p>
        )}
        <ol className="flex flex-col gap-1">
          {ids.map((id, index) => {
            const model = byId.get(id);
            return (
              <li
                className="flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm"
                key={id}
              >
                <span className="w-5 text-muted-foreground">{index + 1}.</span>
                <span className="flex-1 truncate">{model?.name ?? id}</span>
                {index === 0 ? <Badge>Chính</Badge> : <Badge variant="secondary">Dự phòng</Badge>}
                {model && !model.is_active && <Badge variant="outline">Tắt</Badge>}
                <Button
                  aria-label="Lên"
                  disabled={index === 0}
                  onClick={() => setIds(moveModel(ids, index, -1))}
                  size="icon"
                  variant="ghost"
                >
                  <ArrowUpIcon />
                </Button>
                <Button
                  aria-label="Xuống"
                  disabled={index === ids.length - 1}
                  onClick={() => setIds(moveModel(ids, index, 1))}
                  size="icon"
                  variant="ghost"
                >
                  <ArrowDownIcon />
                </Button>
                <Button
                  aria-label={`Bỏ ${model?.name ?? "model"}`}
                  onClick={() => setIds(removeModel(ids, id))}
                  size="icon"
                  variant="ghost"
                >
                  <XIcon />
                </Button>
              </li>
            );
          })}
        </ol>
        <div className="flex flex-wrap items-center gap-2">
          <NativeSelect
            aria-label="Thêm model"
            disabled={addable.length === 0}
            onChange={(event) => {
              if (event.target.value) setIds(addModel(ids, event.target.value));
              event.target.value = "";
            }}
            value=""
          >
            <NativeSelectOption value="">Thêm model…</NativeSelectOption>
            {addable.map((model) => (
              <NativeSelectOption key={model.id} value={model.id}>
                {model.name}
              </NativeSelectOption>
            ))}
          </NativeSelect>
          <div className="flex-1" />
          {changed && (
            <Button onClick={() => setIds(assignment.model_ids)} size="sm" variant="ghost">
              Hoàn tác
            </Button>
          )}
          <Button disabled={!changed || actions.setAssignment.isPending} onClick={save} size="sm">
            Lưu
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
