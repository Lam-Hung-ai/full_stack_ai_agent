"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Message as AGUIMessage } from "@ag-ui/client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import type { ChatStatus } from "ai";
import { v7 as uuidv7 } from "uuid";
import type { ApiError } from "@/lib/api";
import { ASSISTANT_EVENT, ChatAgent, type AssistantEventValue } from "../agent/chat-agent";
import { getHistory } from "../api/conversations-api";
import type { History } from "../types/chat.types";
import { chatKeys } from "./use-conversations";
import { isActive, toAgentMessages, toChatError } from "../utils/history";

const ACTIVE_POLL_MS = 2_000;

/**
 * One conversation: its saved branch, a ChatAgent to continue it, and send.
 *
 * While a turn started elsewhere (another tab, a closed page) is still
 * running, the history is polled until it is saved; live reconnect comes with
 * sprint S5.
 */
export function useConversationChat(conversationId: string) {
  const queryClient = useQueryClient();
  const history = useQuery({
    queryKey: chatKeys.history(conversationId),
    queryFn: ({ signal }) => getHistory(conversationId, signal),
    refetchInterval: (query) =>
      isActive(query.state.data?.data.at(-1)) ? ACTIVE_POLL_MS : false,
  });
  const agentRef = useRef<ChatAgent | null>(null);
  // The branch leaf: parent of the next question (an assistant row id).
  const leafRef = useRef<string | null>(null);
  const [messages, setMessages] = useState<AGUIMessage[] | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [status, setStatus] = useState<ChatStatus>("ready");
  const [error, setError] = useState<ApiError | null>(null);
  const runErrorRef = useRef<ApiError | null>(null);
  const loaded = history.data !== undefined;

  // Coalesce stream updates to one render per animation frame
  // (docs/chat_development/raf-batched-reasoning-updates.md).
  const pendingRef = useRef<AGUIMessage[] | null>(null);
  const frameRef = useRef<number | null>(null);
  const scheduleMessages = useCallback((updated: AGUIMessage[]) => {
    pendingRef.current = updated;
    if (frameRef.current !== null) return;
    frameRef.current = requestAnimationFrame(() => {
      frameRef.current = null;
      if (pendingRef.current) setMessages(pendingRef.current);
    });
  }, []);

  useEffect(() => {
    // Read once per conversation; later refetches go through setMessages below.
    const data = queryClient.getQueryData<History>(chatKeys.history(conversationId));
    if (!loaded || !data) return;
    const agent = new ChatAgent({
      conversationId,
      initialMessages: toAgentMessages(data.data),
    });
    agentRef.current = agent;
    leafRef.current = data.current_message_id;

    const { unsubscribe } = agent.subscribe({
      onMessagesChanged: ({ messages: updated }) => scheduleMessages([...updated]),
      onTextMessageStartEvent: () => setStatus("streaming"),
      onCustomEvent: ({ event }) => {
        if (event.name !== ASSISTANT_EVENT) return;
        const value = event.value as AssistantEventValue;
        // Even a failed or stopped answer is a valid parent for the next question.
        leafRef.current = value.assistantMessageId;
      },
      onRunErrorEvent: ({ event }) => {
        runErrorRef.current = toChatError({
          status: 500,
          payload: { error: { code: event.code ?? "agent_run_failed" } },
        });
      },
    });
    // Deferred: a synchronous setState inside an effect re-renders in a cascade.
    queueMicrotask(() => setIsReady(true));
    return () => {
      unsubscribe();
      setIsReady(false);
      agent.abortRun();
      agentRef.current = null;
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
    };
  }, [conversationId, loaded, queryClient, scheduleMessages]);

  // A turn finished elsewhere: show the saved result.
  useEffect(() => {
    const agent = agentRef.current;
    if (!agent || !history.data || agent.isRunning) return;
    agent.setMessages(toAgentMessages(history.data.data));
    leafRef.current = history.data.current_message_id;
  }, [history.data]);

  const sendMessage = useCallback(
    async (text: string) => {
      const agent = agentRef.current;
      const trimmed = text.trim();
      if (!agent || !trimmed || agent.isRunning) return;
      const id = uuidv7();
      setStatus("submitted");
      setError(null);
      runErrorRef.current = null;
      try {
        await agent.sendMessage({
          parentMessageId: leafRef.current,
          message: { id, text: trimmed, fileIds: [] },
        });
        setError(runErrorRef.current);
        setStatus(runErrorRef.current ? "error" : "ready");
      } catch (caught) {
        // Rejected before streaming (409, network): drop the optimistic row.
        // Never resent automatically (API contract §9).
        agent.setMessages(agent.messages.filter((message) => message.id !== id));
        setError(toChatError(caught));
        setStatus("error");
      } finally {
        await queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      }
    },
    [queryClient],
  );

  const shown = messages ?? (history.data ? toAgentMessages(history.data.data) : []);
  const remoteTurnRunning = isActive(history.data?.data.at(-1)) && status === "ready";
  return {
    messages: shown,
    status,
    error,
    isLoading: history.isLoading,
    isReady,
    loadError: history.error,
    remoteTurnRunning,
    sendMessage,
  };
}
