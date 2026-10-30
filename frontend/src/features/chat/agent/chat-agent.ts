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
 * a plain HttpAgent. History stays on the server: nothing but the new message
 * is sent.
 */

/** Name of the CUSTOM event linking the stream to SQL rows. */
export const ASSISTANT_EVENT = "chat.assistant";

export type AssistantEventValue = {
  conversationId: string;
  userMessageId: string;
  assistantMessageId: string;
  status: "running" | "requires_action" | "completed" | "failed" | "cancelled";
};

export type ChatMessageInput = { id: string; text: string; fileIds: string[] };
export type SendMessageInput = { parentMessageId: string | null; message: ChatMessageInput };
export type EditMessageInput = { userMessageId: string; message: ChatMessageInput };
export type ResumeInput = { assistantMessageId: string; resume: ResumeEntry[] };

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

  sendMessage({ parentMessageId, message }: SendMessageInput): Promise<RunAgentResult> {
    this.addMessage({ id: message.id, role: "user", content: message.text });
    return this.runOperation({
      path: "/messages",
      body: { parent_message_id: parentMessageId, message: toDto(message) },
    });
  }

  /** Ask a new version of a question; the old version keeps its branch. */
  editMessage({ userMessageId, message }: EditMessageInput): Promise<RunAgentResult> {
    this.addMessage({ id: message.id, role: "user", content: message.text });
    return this.runOperation({
      path: `/messages/${userMessageId}/edit`,
      body: { message: toDto(message) },
    });
  }

  /** Answer what a paused assistant waits on; the same turn continues. */
  resume({ assistantMessageId, resume }: ResumeInput): Promise<RunAgentResult> {
    return this.runOperation({ path: `/messages/${assistantMessageId}/resume`, body: { resume } }, resume);
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

  /** Answer the question of `assistantMessageId` again, beside that answer. */
  regenerate({ assistantMessageId }: { assistantMessageId: string }): Promise<RunAgentResult> {
    return this.runOperation({ path: `/messages/${assistantMessageId}/regenerate` });
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

function toDto(message: ChatMessageInput) {
  return { id: message.id, text: message.text, file_ids: message.fileIds };
}
