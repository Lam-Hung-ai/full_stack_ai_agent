"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createConnection,
  createModel,
  deleteConnection,
  deleteModel,
  getAssignments,
  getConnections,
  getModels,
  getProviders,
  setAssignment,
  testModel,
  updateConnection,
  updateModel,
} from "../api/llm-api";
import type {
  LlmConnectionCreate,
  LlmConnectionUpdate,
  LlmModelCreate,
  LlmModelUpdate,
} from "../types/llm.types";

export const llmKeys = {
  all: ["admin", "llm"] as const,
  providers: () => [...llmKeys.all, "providers"] as const,
  connections: () => [...llmKeys.all, "connections"] as const,
  models: () => [...llmKeys.all, "models"] as const,
  assignments: () => [...llmKeys.all, "assignments"] as const,
};

export function useProviders() {
  return useQuery({
    queryKey: llmKeys.providers(),
    queryFn: ({ signal }) => getProviders(signal),
    // Installed packages change only with a deployment.
    staleTime: Infinity,
  });
}

export function useConnections() {
  return useQuery({
    queryKey: llmKeys.connections(),
    queryFn: ({ signal }) => getConnections(signal),
  });
}

export function useModels() {
  return useQuery({ queryKey: llmKeys.models(), queryFn: ({ signal }) => getModels(signal) });
}

export function useAssignments() {
  return useQuery({
    queryKey: llmKeys.assignments(),
    queryFn: ({ signal }) => getAssignments(signal),
  });
}

/** Writes of the LLM admin page; each refreshes the lists it changes. */
export function useLlmActions() {
  const queryClient = useQueryClient();
  const refresh =
    (...keys: (readonly string[])[]) =>
    () =>
      Promise.all(keys.map((queryKey) => queryClient.invalidateQueries({ queryKey })));

  return {
    createConnection: useMutation({
      mutationFn: (input: LlmConnectionCreate) => createConnection(input),
      onSuccess: refresh(llmKeys.connections()),
    }),
    updateConnection: useMutation({
      mutationFn: ({ id, input }: { id: string; input: LlmConnectionUpdate }) =>
        updateConnection(id, input),
      onSuccess: refresh(llmKeys.connections()),
    }),
    deleteConnection: useMutation({
      mutationFn: (id: string) => deleteConnection(id),
      onSuccess: refresh(llmKeys.connections()),
    }),
    createModel: useMutation({
      mutationFn: (input: LlmModelCreate) => createModel(input),
      onSuccess: refresh(llmKeys.models()),
    }),
    updateModel: useMutation({
      mutationFn: ({ id, input }: { id: string; input: LlmModelUpdate }) => updateModel(id, input),
      onSuccess: refresh(llmKeys.models()),
    }),
    deleteModel: useMutation({
      mutationFn: (id: string) => deleteModel(id),
      onSuccess: refresh(llmKeys.models()),
    }),
    testModel: useMutation({ mutationFn: (id: string) => testModel(id) }),
    setAssignment: useMutation({
      mutationFn: ({ purpose, modelIds }: { purpose: string; modelIds: string[] }) =>
        setAssignment(purpose, modelIds),
      onSuccess: refresh(llmKeys.assignments()),
    }),
  };
}
