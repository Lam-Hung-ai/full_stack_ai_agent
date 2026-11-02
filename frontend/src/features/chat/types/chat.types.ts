import type { Message } from "@ag-ui/client";
import type { components } from "@/generated/api/schema";

export type Conversation = components["schemas"]["ConversationResponse"];
export type ConversationListItem = components["schemas"]["ConversationListItem"];
export type ConversationList = components["schemas"]["ConversationListResponse"];
export type ConversationUpdate = components["schemas"]["ConversationUpdate"];
export type ConversationSearch = components["schemas"]["ConversationSearchResponse"];
export type ConversationSearchItem = components["schemas"]["ConversationSearchItem"];
export type History = components["schemas"]["HistoryResponse"];
export type TurnRow = components["schemas"]["TurnResponse"];
export type TurnStatus = TurnRow["status"];
export type StopResult = components["schemas"]["StopResponse"];
export type Folder = components["schemas"]["FolderResponse"];
export type FolderList = components["schemas"]["FolderListResponse"];

/** Which chats a sidebar list shows. */
/** Order after pinned chats: newest activity or newest created. */
export type ConversationSort = "updated" | "created";

/** A sidebar list: pinned and recent hold the chats outside folders. */
export type ConversationFilter =
  | { kind: "pinned" }
  | { kind: "recent"; sort: ConversationSort }
  | { kind: "folder"; folderId: string }
  | { kind: "archived"; sort: ConversationSort };

/**
 * One SQL row as rendered: a user question or a whole assistant turn, whose
 * `content` is its AG-UI bundle. `live` marks the turn this tab is streaming.
 */
export type RowView = {
  id: string;
  role: TurnRow["role"];
  status: TurnStatus;
  content: Message[];
  siblingIds: string[];
  /** When the turn was saved; absent while this tab is still sending it. */
  createdAt?: string;
  /** Last change; for a finished turn, when it ended. */
  updatedAt?: string;
  live?: boolean;
};

/** A turn this tab started and is streaming, drawn over the saved branch. */
export type LiveTurn = {
  /** Rows of the shown branch kept above the new turn. */
  kept: RowView[];
  /** The new question (send, edit); none for a regeneration or a resume. */
  question: RowView | null;
  /** Protocol id of the question being answered; the answer streams after it. */
  questionId: string;
  /** Resume: the paused row this turn continues; its content stays first. */
  continued: RowView | null;
  assistantId: string | null;
  status: TurnStatus;
};
