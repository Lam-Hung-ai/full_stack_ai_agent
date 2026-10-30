"use client";

import type { Message as AGUIMessage } from "@ag-ui/client";
import type { ToolUIPart } from "ai";
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import { Loader } from "@/components/ai-elements/loader";
import { Message, MessageContent, MessageResponse } from "@/components/ai-elements/message";
import { Reasoning, ReasoningContent, ReasoningTrigger } from "@/components/ai-elements/reasoning";
import { Tool, ToolContent, ToolHeader, ToolInput, ToolOutput } from "@/components/ai-elements/tool";
import { buildTurns, findToolResult, parseToolArgs, type Turn } from "../utils/agui-messages";
import { ReasoningSummary } from "./reasoning-summary";

/** The rendered turns of a conversation; `empty` shows when there are none. */
export function ChatMessages({
  messages,
  isBusy,
  empty,
}: {
  messages: readonly AGUIMessage[];
  isBusy: boolean;
  empty?: React.ReactNode;
}) {
  const turns = buildTurns(messages);
  return (
    <Conversation>
      <ConversationContent>
        {turns.length === 0
          ? empty
          : turns.map((turn, index) => (
              <TurnView
                isStreaming={isBusy && index === turns.length - 1}
                key={turn.message.id}
                messages={messages}
                turn={turn}
              />
            ))}
      </ConversationContent>
      <ConversationScrollButton />
    </Conversation>
  );
}

function TurnView({
  turn: { message, reasoning },
  messages,
  isStreaming,
}: {
  turn: Turn;
  messages: readonly AGUIMessage[];
  isStreaming: boolean;
}) {
  if (message.role === "user") {
    return (
      <Message from="user">
        <MessageContent>
          <MessageResponse>{typeof message.content === "string" ? message.content : ""}</MessageResponse>
        </MessageContent>
      </Message>
    );
  }

  const toolCalls = message.toolCalls ?? [];
  const isReasoningStreaming = isStreaming && !message.content && toolCalls.length === 0;

  return (
    <Message from="assistant">
      <MessageContent>
        {reasoning && (
          <Reasoning defaultOpen={isReasoningStreaming} isStreaming={isReasoningStreaming}>
            <ReasoningTrigger>
              <ReasoningSummary isStreaming={isReasoningStreaming} reasoning={reasoning} />
            </ReasoningTrigger>
            <ReasoningContent>{reasoning}</ReasoningContent>
          </Reasoning>
        )}
        {message.content ? (
          <MessageResponse>{message.content}</MessageResponse>
        ) : toolCalls.length === 0 && !reasoning && isStreaming ? (
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
              <ToolHeader state={state} type={`tool-${toolCall.function.name}` as ToolUIPart["type"]} />
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
}
