"use client";

import { SparklesIcon } from "lucide-react";
import type { ToolUIPart } from "ai";
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
import { Reasoning, ReasoningContent, ReasoningTrigger } from "@/components/ai-elements/reasoning";
import { Tool, ToolContent, ToolHeader, ToolInput, ToolOutput } from "@/components/ai-elements/tool";
import { ReasoningSummary } from "@/components/chat/reasoning-summary";
import { useAgentChat } from "@/hooks/use-agent-chat";
import { buildTurns, findToolResult, parseToolArgs } from "@/lib/agui-messages";

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
