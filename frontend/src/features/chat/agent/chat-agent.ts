import {
  HttpAgent,
  runHttpRequest,
  transformHttpEventStream,
  type Message,
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
  status: "running" | "completed" | "failed" | "cancelled";
};

export type ChatMessageInput = { id: string; text: string; fileIds: string[] };
export type SendMessageInput = { parentMessageId: string | null; message: ChatMessageInput };

type Operation = { path: string; body: unknown };
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
      body: {
        parent_message_id: parentMessageId,
        message: { id: message.id, text: message.text, file_ids: message.fileIds },
      },
    });
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
            body: JSON.stringify(operation.body),
            signal: this.abortController.signal,
          })
        : Promise.reject(new Error("ChatAgent runs only through its operation methods"));
    return transformHttpEventStream(runHttpRequest(request), this.debugLogger);
  }

  private runOperation(operation: Operation): Promise<RunAgentResult> {
    return this.runAgent({ forwardedProps: { [OPERATION]: operation } });
  }
}
