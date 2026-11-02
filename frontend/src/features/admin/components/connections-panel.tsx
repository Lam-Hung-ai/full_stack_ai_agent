"use client";

import { useState } from "react";
import { PencilIcon, PlusIcon, Trash2Icon } from "lucide-react";
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
import { useConnections, useLlmActions, useProviders } from "../hooks/use-llm";
import type { ConnectionValues } from "../schemas/llm.schema";
import type { LlmConnection, LlmConnectionUpdate } from "../types/llm.types";
import { llmErrorMessage } from "../utils/error-message";
import { parseSettings } from "../utils/settings";
import { ConnectionDialog } from "./connection-dialog";

type Editing = { mode: "create" } | { mode: "edit"; connection: LlmConnection };

export function ConnectionsPanel() {
  const connections = useConnections();
  const providers = useProviders();
  const actions = useLlmActions();
  const [editing, setEditing] = useState<Editing | null>(null);
  const [deleting, setDeleting] = useState<LlmConnection | null>(null);
  const save = editing?.mode === "edit" ? actions.updateConnection : actions.createConnection;

  const submit = (values: ConnectionValues) => {
    const onSuccess = () => setEditing(null);
    const clientParams = parseSettings(values.clientParams) ?? {};
    if (editing?.mode !== "edit") {
      actions.createConnection.mutate(
        {
          key: values.key,
          name: values.name,
          provider: values.provider,
          client_params: clientParams,
          api_key: values.apiKey || null,
          is_active: values.isActive,
        },
        { onSuccess },
      );
      return;
    }
    const input: LlmConnectionUpdate = {
      name: values.name,
      provider: values.provider,
      client_params: clientParams,
      is_active: values.isActive,
    };
    // Omitted keeps the stored key; null clears it.
    if (values.clearApiKey) input.api_key = null;
    else if (values.apiKey) input.api_key = values.apiKey;
    actions.updateConnection.mutate({ id: editing.connection.id, input }, { onSuccess });
  };

  if (connections.isPending || providers.isPending)
    return <Spinner aria-label="Đang tải kết nối" />;
  if (connections.isError || providers.isError) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{llmErrorMessage(connections.error ?? providers.error)}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex justify-end">
        <Button onClick={() => setEditing({ mode: "create" })} size="sm">
          <PlusIcon />
          Tạo kết nối
        </Button>
      </div>
      {actions.deleteConnection.isError && (
        <Alert variant="destructive">
          <AlertDescription>{llmErrorMessage(actions.deleteConnection.error)}</AlertDescription>
        </Alert>
      )}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Kết nối</TableHead>
            <TableHead>Provider</TableHead>
            <TableHead>API key</TableHead>
            <TableHead className="w-24" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {connections.data.data.length === 0 && (
            <TableRow>
              <TableCell className="text-muted-foreground" colSpan={4}>
                Chưa có kết nối. Agent đang dùng cấu hình biến môi trường.
              </TableCell>
            </TableRow>
          )}
          {connections.data.data.map((connection) => (
            <TableRow key={connection.id}>
              <TableCell>
                <div className="flex items-center gap-2 font-medium">
                  {connection.name}
                  {!connection.is_active && <Badge variant="secondary">Tắt</Badge>}
                </div>
                <div className="text-muted-foreground text-xs">{connection.key}</div>
              </TableCell>
              <TableCell>{connection.provider}</TableCell>
              <TableCell className="font-mono text-xs">
                {connection.has_api_key ? `…${connection.api_key_hint}` : "—"}
              </TableCell>
              <TableCell>
                <div className="flex justify-end gap-1">
                  <Button
                    aria-label={`Sửa kết nối ${connection.name}`}
                    onClick={() => setEditing({ mode: "edit", connection })}
                    size="icon"
                    variant="ghost"
                  >
                    <PencilIcon />
                  </Button>
                  <Button
                    aria-label={`Xoá kết nối ${connection.name}`}
                    onClick={() => setDeleting(connection)}
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
        <ConnectionDialog
          connection={editing.mode === "edit" ? editing.connection : undefined}
          error={save.isError ? llmErrorMessage(save.error) : null}
          isPending={save.isPending}
          onClose={() => {
            save.reset();
            setEditing(null);
          }}
          onSubmit={submit}
          providers={providers.data.data}
        />
      )}
      {deleting && (
        <ConfirmDialog
          description={`Kết nối ${deleting.name} và API key đã lưu sẽ bị xoá.`}
          onClose={() => setDeleting(null)}
          onConfirm={() => {
            actions.deleteConnection.mutate(deleting.id);
            setDeleting(null);
          }}
          title="Xoá kết nối?"
        />
      )}
    </div>
  );
}
