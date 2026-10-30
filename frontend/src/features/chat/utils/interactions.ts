import type { ResumeEntry } from "@ag-ui/client";
import type { RowView } from "../types/chat.types";
import type { ActivityMessage } from "./agui-messages";

/**
 * Activities `user_interaction` (database phase 4 §5): what a paused turn
 * asks the user, and the answer once given. Written by the backend; the UI
 * only reads them and answers through resume.
 */
export const INTERACTION_ACTIVITY = "user_interaction";
/** The tool the agent asks through; its card is the activity, not a tool card. */
export const ASK_USER_TOOL = "ask_user";

export type Interaction = {
  action_id: string;
  interrupt_id: string;
  kind: "user_question" | "tool_approval" | string;
  status: "waiting" | "answered" | "cancelled";
  question?: string;
  tool_name?: string;
  arguments?: unknown;
  response?: unknown;
};

/** What the user sends for one interrupt (the ResumeEntry payload). */
export type InteractionAnswer = { answer: string } | { approved: boolean };

export function interactionOf(message: ActivityMessage): Interaction | null {
  if (message.activityType !== INTERACTION_ACTIVITY) return null;
  const content = message.content as Partial<Interaction> | undefined;
  return content?.interrupt_id && content.status ? (content as Interaction) : null;
}

/** Interactions of a row still waiting for an answer. */
export function waitingInteractions(row: RowView): Interaction[] {
  return row.content.flatMap((message) => {
    if (message.role !== "activity") return [];
    const interaction = interactionOf(message);
    return interaction?.status === "waiting" ? [interaction] : [];
  });
}

export function toResumeEntries(answers: Record<string, InteractionAnswer>): ResumeEntry[] {
  return Object.entries(answers).map(([interruptId, payload]) => ({
    interruptId,
    status: "resolved",
    payload,
  }));
}

/** The row as it reads once answered, before the server confirms it. */
export function withAnswers(row: RowView, answers: Record<string, InteractionAnswer>): RowView {
  return {
    ...row,
    status: "running",
    content: row.content.map((message) => {
      if (message.role !== "activity") return message;
      const interaction = interactionOf(message);
      const answer = interaction && answers[interaction.interrupt_id];
      if (!answer) return message;
      const response = "answer" in answer ? answer.answer : answer;
      return { ...message, content: { ...interaction, status: "answered", response } };
    }),
  };
}
