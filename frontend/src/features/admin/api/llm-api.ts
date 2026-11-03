import { apiClient } from "@/lib/api";
import type {
  LlmAssignment,
  LlmConnection,
  LlmConnectionCreate,
  LlmConnectionUpdate,
  LlmModel,
  LlmModelCreate,
  LlmModelTest,
  LlmModelUpdate,
  LlmProvider,
} from "../types/llm.types";

const base = "/api/v1/admin/llm";

export function getProviders(signal?: AbortSignal) {
  return apiClient<{ data: LlmProvider[] }>(`${base}/providers`, { signal });
}

export function getConnections(signal?: AbortSignal) {
  return apiClient<{ data: LlmConnection[] }>(`${base}/connections`, { signal });
}

export function createConnection(input: LlmConnectionCreate) {
  return apiClient<LlmConnection>(`${base}/connections`, { method: "POST", body: input });
}

export function updateConnection(connectionId: string, input: LlmConnectionUpdate) {
  return apiClient<LlmConnection>(`${base}/connections/${connectionId}`, {
    method: "PATCH",
    body: input,
  });
}

export function deleteConnection(connectionId: string) {
  return apiClient<void>(`${base}/connections/${connectionId}`, { method: "DELETE" });
}

export function getModels(signal?: AbortSignal) {
  return apiClient<{ data: LlmModel[] }>(`${base}/models`, { signal });
}

export function createModel(input: LlmModelCreate) {
  return apiClient<LlmModel>(`${base}/models`, { method: "POST", body: input });
}

export function updateModel(modelId: string, input: LlmModelUpdate) {
  return apiClient<LlmModel>(`${base}/models/${modelId}`, { method: "PATCH", body: input });
}

export function deleteModel(modelId: string) {
  return apiClient<void>(`${base}/models/${modelId}`, { method: "DELETE" });
}

export function testModel(modelId: string) {
  return apiClient<LlmModelTest>(`${base}/models/${modelId}/test`, { method: "POST" });
}

export function getAssignments(signal?: AbortSignal) {
  return apiClient<{ data: LlmAssignment[] }>(`${base}/assignments`, { signal });
}

export function setAssignment(purpose: string, modelIds: string[]) {
  return apiClient<LlmAssignment>(`${base}/assignments/${purpose}`, {
    method: "PUT",
    body: { model_ids: modelIds },
  });
}
