import {
  HttpAgent,
  runHttpRequest,
  transformHttpEventStream,
  type Message,
  type ResumeEntry,
  type RunAgentInput,
  type RunAgentResult,
} from "@ag-ui/client";
import { apiUrl, authorizedFetch } from "@/lib/api";

/**
 * AG-UI agent bound to one conversation (chat-agent-client-decisions.md).
 *
 * Requests use the application's own DTOs; responses are AG-UI SSE parsed and
 * applied by the SDK pipeline, so messages, state and subscribers work as with
 * a plain HttpAgent. History stays on the server: nothing but the new turn
 * is sent.
 */

/** Name of the CUSTOM event linking the stream to SQL rows. */
export const TURN_EVENT = "chat.turn";

export type TurnEventValue = {
  conversationId: string;
  userTurnId: string;
  assistantTurnId: string;
  status: "running" | "requires_action" | "completed" | "failed" | "cancelled";
};

export type TurnInput = { id: string; text: string; fileIds: string[] };
export type SendTurnInput = { parentTurnId: string | null; turn: TurnInput };
export type EditTurnInput = { userTurnId: string; turn: TurnInput };
export type ResumeInput = { assistantTurnId: string; resume: ResumeEntry[] };

type Operation = { path: string; body?: unknown };
// The operation travels inside the run's own input, so a second call can
// never rewrite the request of one still running.
const OPERATION = "chatOperation";

export class ChatAgent extends HttpAgent {
  readonly conversationId: string;

  constructor({
    conversationId,
    initialMessages,
  }: {
    conversationId: string;
    initialMessages?: Message[];
  }) {
    super({
      url: apiUrl(`/api/v1/conversations/${conversationId}`),
      threadId: conversationId,
      initialMessages,
      fetch: authorizedFetch,
    });
    this.conversationId = conversationId;
  }

  sendTurn({ parentTurnId, turn }: SendTurnInput): Promise<RunAgentResult> {
    this.addMessage({ id: turn.id, role: "user", content: turn.text });
    return this.runOperation({
      path: "/turns",
      body: { parent_turn_id: parentTurnId, turn: toDto(turn) },
    });
  }

  /** Ask a new version of a question; the old version keeps its branch. */
  editTurn({ userTurnId, turn }: EditTurnInput): Promise<RunAgentResult> {
    this.addMessage({ id: turn.id, role: "user", content: turn.text });
    return this.runOperation({
      path: `/turns/${userTurnId}/edit`,
      body: { turn: toDto(turn) },
    });
  }

  /** Answer what a paused assistant waits on; the same turn continues. */
  resume({ assistantTurnId, resume }: ResumeInput): Promise<RunAgentResult> {
    return this.runOperation({ path: `/turns/${assistantTurnId}/resume`, body: { resume } }, resume);
  }

  /**
   * Follow the chat as it is now (API §6): a snapshot, then the running turn
   * if there is one. Read only; one stream per tab (QD-23).
   */
  attach(): Promise<RunAgentResult> {
    this.pendingInterrupts = [];
    // HttpAgent renews its controller in runAgent only.
    this.abortController = new AbortController();
    return this.connectAgent();
  }

  protected connect(): ReturnType<HttpAgent["run"]> {
    const request = () =>
      this.fetch(`${this.url}/connect`, {
        method: "POST",
        headers: { ...this.headers, Accept: "text/event-stream" },
        signal: this.abortController.signal,
      });
    return transformHttpEventStream(runHttpRequest(request), this.debugLogger);
  }

  /** Answer the question of `assistantTurnId` again, beside that answer. */
  regenerate({ assistantTurnId }: { assistantTurnId: string }): Promise<RunAgentResult> {
    return this.runOperation({ path: `/turns/${assistantTurnId}/regenerate` });
  }

  run(input: RunAgentInput): ReturnType<HttpAgent["run"]> {
    const operation = input.forwardedProps?.[OPERATION] as Operation | undefined;
    const request = () =>
      operation
        ? this.fetch(`${this.url}${operation.path}`, {
            method: "POST",
            headers: {
              ...this.headers,
              "Content-Type": "application/json",
              Accept: "text/event-stream",
            },
            body: operation.body === undefined ? undefined : JSON.stringify(operation.body),
            signal: this.abortController.signal,
          })
        : Promise.reject(new Error("ChatAgent runs only through its operation methods"));
    return transformHttpEventStream(runHttpRequest(request), this.debugLogger);
  }

  private runOperation(operation: Operation, resume?: ResumeEntry[]): Promise<RunAgentResult> {
    // The server owns what a turn waits on and checks every answer (API §5).
    // The SDK's own bookkeeping from an interrupt outcome would refuse a stop
    // followed by a new question, or an answer given after a reload.
    this.pendingInterrupts = [];
    return this.runAgent({ forwardedProps: { [OPERATION]: operation }, resume });
  }
}

function toDto(turn: TurnInput) {
  return { id: turn.id, text: turn.text, file_ids: turn.fileIds };
}
