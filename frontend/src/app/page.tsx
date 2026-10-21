"use client";

import { BrainIcon, ChevronDownIcon, SparklesIcon } from "lucide-react";
import type { ToolUIPart } from "ai";
import type { Message as AGUIMessage } from "@ag-ui/client";
import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import { Message, MessageContent, MessageResponse } from "@/components/ai-elements/message";
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  PromptInputSubmit,
  PromptInputTextarea,
} from "@/components/ai-elements/prompt-input";
import { Loader } from "@/components/ai-elements/loader";
import {
  Reasoning,
  ReasoningContent,
  ReasoningTrigger,
  useReasoning,
} from "@/components/ai-elements/reasoning";
import { Tool, ToolContent, ToolHeader, ToolInput, ToolOutput } from "@/components/ai-elements/tool";
import { useAgentChat } from "@/hooks/use-agent-chat";
import { cn } from "@/lib/utils";

type TurnMessage = Extract<AGUIMessage, { role: "user" | "assistant" }>;
type Turn = { message: TurnMessage; reasoning?: string };

// AG-UI streams a standalone `reasoning` message before the `assistant` message
// it belongs to (no shared id), so pair each one with the assistant turn that follows it.
function buildTurns(messages: AGUIMessage[]): Turn[] {
  const turns: Turn[] = [];
  let pendingReasoning: string | undefined;

  for (const message of messages) {
    if (message.role === "reasoning") {
      pendingReasoning = message.content;
      continue;
    }
    if (message.role === "user" || message.role === "assistant") {
      turns.push({ message, reasoning: message.role === "assistant" ? pendingReasoning : undefined });
      pendingReasoning = undefined;
    }
  }

  // The assistant message doesn't exist yet while reasoning is still streaming
  // (TEXT_MESSAGE_START only fires after REASONING_END), so without this the
  // entire reasoning phase renders nothing — reasoning only became visible once
  // the run finished. Render a placeholder turn so it shows up immediately.
  if (pendingReasoning !== undefined) {
    turns.push({
      message: { id: "__pending-reasoning__", role: "assistant", content: "" },
      reasoning: pendingReasoning,
    });
  }

  return turns;
}

function findToolResult(messages: AGUIMessage[], toolCallId: string) {
  return messages.find((m) => m.role === "tool" && m.toolCallId === toolCallId) as
    | Extract<AGUIMessage, { role: "tool" }>
    | undefined;
}

function parseToolArgs(raw: string): unknown {
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

// While collapsed, show the latest non-blank line instead of a static "Thinking..."
// label — a stalled model visibly stalls, a fast one visibly moves, without
// needing to expand the panel to tell the difference.
function latestLine(text: string): string {
  const visible = text.trimEnd();
  const newline = visible.lastIndexOf("\n");
  return newline === -1 ? visible : visible.slice(newline + 1);
}

function ReasoningSummary({ reasoning, isStreaming }: { reasoning: string; isStreaming: boolean }) {
  const { isOpen } = useReasoning();

  return (
    <>
      <BrainIcon className="size-4 shrink-0" />
      {isStreaming ? (
        <span className="min-w-0 flex-1 truncate text-left">{latestLine(reasoning)}</span>
      ) : (
        <span>Thought for a few seconds</span>
      )}
      <ChevronDownIcon
        className={cn("size-4 shrink-0 transition-transform", isOpen ? "rotate-180" : "rotate-0")}
      />
    </>
  );
}

export default function Home() {
  const { messages, status, sendMessage } = useAgentChat();
  const turns = buildTurns(messages);
  const isBusy = status === "submitted" || status === "streaming";

  return (
    <div className="mx-auto flex h-dvh w-full max-w-3xl flex-col p-4">
      <Conversation>
        <ConversationContent>
          {turns.length === 0 ? (
            <ConversationEmptyState
              description="Hỏi bất cứ điều gì — được trả lời bởi agent FastAPI + LangGraph qua AG-UI protocol."
              icon={<SparklesIcon className="size-6" />}
              title="Agent Chat"
            />
          ) : (
            turns.map(({ message, reasoning }, index) => {
              if (message.role === "user") {
                return (
                  <Message from="user" key={message.id}>
                    <MessageContent>
                      <MessageResponse>
                        {typeof message.content === "string" ? message.content : ""}
                      </MessageResponse>
                    </MessageContent>
                  </Message>
                );
              }

              const toolCalls = message.toolCalls ?? [];
              const isLastTurn = index === turns.length - 1;
              const isReasoningStreaming = isBusy && isLastTurn && !message.content && toolCalls.length === 0;

              return (
                <Message from="assistant" key={message.id}>
                  <MessageContent>
                    {reasoning && (
                      <Reasoning isStreaming={isReasoningStreaming}>
                        <ReasoningTrigger>
                          <ReasoningSummary isStreaming={isReasoningStreaming} reasoning={reasoning} />
                        </ReasoningTrigger>
                        <ReasoningContent>{reasoning}</ReasoningContent>
                      </Reasoning>
                    )}
                    {message.content ? (
                      <MessageResponse>{message.content}</MessageResponse>
                    ) : toolCalls.length === 0 && !reasoning ? (
                      <Loader />
                    ) : null}
                    {toolCalls.map((toolCall) => {
                      const result = findToolResult(messages, toolCall.id);
                      const state: ToolUIPart["state"] = result
                        ? result.error
                          ? "output-error"
                          : "output-available"
                        : "input-available";

                      return (
                        <Tool key={toolCall.id}>
                          <ToolHeader
                            state={state}
                            type={`tool-${toolCall.function.name}` as ToolUIPart["type"]}
                          />
                          <ToolContent>
                            <ToolInput input={parseToolArgs(toolCall.function.arguments)} />
                            <ToolOutput
                              errorText={result?.error}
                              output={typeof result?.content === "string" ? result.content : undefined}
                            />
                          </ToolContent>
                        </Tool>
                      );
                    })}
                  </MessageContent>
                </Message>
              );
            })
          )}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      <PromptInput className="mt-4" onSubmit={(message) => sendMessage(message.text)}>
        <PromptInputBody>
          <PromptInputTextarea />
        </PromptInputBody>
        <PromptInputFooter>
          <span className="text-muted-foreground text-xs">
            Enter để gửi, Shift+Enter để xuống dòng
          </span>
          <PromptInputSubmit status={status} />
        </PromptInputFooter>
      </PromptInput>
    </div>
  );
}
