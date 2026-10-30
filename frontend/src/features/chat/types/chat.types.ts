import type { components } from "@/generated/api/schema";

export type Conversation = components["schemas"]["ConversationResponse"];
export type ConversationListItem = components["schemas"]["ConversationListItem"];
export type ConversationList = components["schemas"]["ConversationListResponse"];
export type History = components["schemas"]["HistoryResponse"];
export type MessageRow = components["schemas"]["MessageResponse"];
export type MessageStatus = MessageRow["status"];
