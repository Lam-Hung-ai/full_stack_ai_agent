import type { Message } from "@ag-ui/client";
import type { components } from "@/generated/api/schema";

export type Conversation = components["schemas"]["ConversationResponse"];
export type ConversationListItem = components["schemas"]["ConversationListItem"];
export type ConversationList = components["schemas"]["ConversationListResponse"];
export type ConversationUpdate = components["schemas"]["ConversationUpdate"];
export type History = components["schemas"]["HistoryResponse"];
export type MessageRow = components["schemas"]["MessageResponse"];
export type MessageStatus = MessageRow["status"];
export type StopResult = components["schemas"]["StopResponse"];
export type Folder = components["schemas"]["FolderResponse"];
export type FolderList = components["schemas"]["FolderListResponse"];

/** Which chats a sidebar list shows. */
export type ConversationFilter =
  | { kind: "unfiled" }
  | { kind: "folder"; folderId: string }
  | { kind: "archived" };

/**
 * One SQL row as rendered: a user question or a whole assistant turn, whose
 * `content` is its AG-UI bundle. `live` marks the turn this tab is streaming.
 */
export type RowView = {
  id: string;
  role: MessageRow["role"];
  status: MessageStatus;
  content: Message[];
  siblingIds: string[];
  live?: boolean;
};

/** A turn this tab started and is streaming, drawn over the saved branch. */
export type LiveTurn = {
  /** Rows of the shown branch kept above the new turn. */
  kept: RowView[];
  /** The new question (send, edit); none for a regeneration. */
  question: RowView | null;
  /** Protocol id of the question being answered; the answer streams after it. */
  questionId: string;
  assistantId: string | null;
  status: MessageStatus;
  /** The stream ended; shown until the saved branch has the assistant row. */
  done: boolean;
};
