import type { components } from "@/generated/api/schema";

type Schemas = components["schemas"];

export type LlmProvider = Schemas["ProviderResponse"];
export type LlmConnection = Schemas["ConnectionResponse"];
export type LlmConnectionCreate = Schemas["ConnectionCreate"];
export type LlmConnectionUpdate = Schemas["ConnectionUpdate"];
export type LlmModel = Schemas["ModelResponse"];
export type LlmModelCreate = Schemas["ModelCreate"];
export type LlmModelUpdate = Schemas["ModelUpdate"];
export type LlmAssignment = Schemas["AssignmentResponse"];
export type LlmModelTest = Schemas["ModelTestResponse"];
