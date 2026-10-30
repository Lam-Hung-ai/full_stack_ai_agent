"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Message as AGUIMessage } from "@ag-ui/client";
import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ChatStatus } from "ai";
import { v7 as uuidv7 } from "uuid";
import type { ApiError } from "@/lib/api";
import { ASSISTANT_EVENT, ChatAgent, type AssistantEventValue } from "../agent/chat-agent";
import { getHistory, stopAssistant } from "../api/conversations-api";
import type { LiveTurn, RowView } from "../types/chat.types";
import { isActive, shownRows, toChatError, toRowView } from "../utils/history";
import {
  type InteractionAnswer,
  toResumeEntries,
  waitingInteractions,
  withAnswers,
} from "../utils/interactions";
import { chatKeys } from "./use-conversations";

const ACTIVE_POLL_MS = 2_000;

type TurnStart = Pick<LiveTurn, "kept" | "question" | "questionId"> & {
  continued?: RowView;
};

function questionRow(id: string, text: string, siblingIds: string[]): RowView {
  return {
    id,
    role: "user",
    status: "completed",
    content: [{ id, role: "user", content: text }],
    siblingIds,
  };
}

/**
 * One conversation: the branch this tab shows, a ChatAgent to continue it,
 * and the turn actions (send, edit, regenerate, answer a pause, stop, switch
 * branch).
 *
 * Which branch is shown is per tab (API §2): `anchor` opens the branch
 * through a message, null the saved one. A turn this tab streams is drawn
 * over that branch until the saved branch holds its answer. While a turn
 * started elsewhere is still running, the history is polled until it is
 * saved; live reconnect comes with sprint S5.
 */
export function useConversationChat(conversationId: string) {
  const queryClient = useQueryClient();
  const [anchor, setAnchor] = useState<string | null>(null);
  const runningRef = useRef(false);
  const history = useQuery({
    queryKey: chatKeys.history(conversationId, anchor),
    queryFn: ({ signal }) => getHistory(conversationId, { fromMessageId: anchor, signal }),
    placeholderData: keepPreviousData,
    refetchInterval: (query) =>
      isActive(query.state.data?.data.at(-1)) && !runningRef.current ? ACTIVE_POLL_MS : false,
  });
  const agentRef = useRef<ChatAgent | null>(null);
  const liveRef = useRef<LiveTurn | null>(null);
  const [live, setLive] = useState<LiveTurn | null>(null);
  const [liveMessages, setLiveMessages] = useState<AGUIMessage[]>([]);
  const [agentReady, setAgentReady] = useState(false);
  const [status, setStatus] = useState<ChatStatus>("ready");
  const [error, setError] = useState<ApiError | null>(null);
  // Answers given so far when one pause asks several things at once.
  const [drafts, setDrafts] = useState<Record<string, InteractionAnswer>>({});
  const runErrorRef = useRef<ApiError | null>(null);

  const updateLive = useCallback((next: (current: LiveTurn | null) => LiveTurn | null) => {
    liveRef.current = next(liveRef.current);
    setLive(liveRef.current);
  }, []);

  // Coalesce stream updates to one render per animation frame
  // (docs/chat_development/raf-batched-reasoning-updates.md).
  const pendingRef = useRef<AGUIMessage[] | null>(null);
  const frameRef = useRef<number | null>(null);
  const scheduleMessages = useCallback((updated: AGUIMessage[]) => {
    pendingRef.current = updated;
    if (frameRef.current !== null) return;
    frameRef.current = requestAnimationFrame(() => {
      frameRef.current = null;
      if (pendingRef.current) setLiveMessages(pendingRef.current);
    });
  }, []);

  useEffect(() => {
    const agent = new ChatAgent({ conversationId });
    agentRef.current = agent;
    const { unsubscribe } = agent.subscribe({
      onMessagesChanged: ({ messages: updated }) => scheduleMessages([...updated]),
      onTextMessageStartEvent: () => setStatus("streaming"),
      onCustomEvent: ({ event }) => {
        if (event.name !== ASSISTANT_EVENT) return;
        const value = event.value as AssistantEventValue;
        updateLive(
          (current) =>
            current && { ...current, assistantId: value.assistantMessageId, status: value.status },
        );
      },
      onRunErrorEvent: ({ event }) => {
        runErrorRef.current = toChatError({
          status: 500,
          payload: { error: { code: event.code ?? "agent_run_failed" } },
        });
      },
    });
    // Deferred: a synchronous setState inside an effect re-renders in a cascade.
    queueMicrotask(() => setAgentReady(true));
    return () => {
      unsubscribe();
      setAgentReady(false);
      agent.abortRun();
      agentRef.current = null;
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
    };
  }, [conversationId, scheduleMessages, updateLive]);

  const saved = useMemo(() => history.data?.data.map(toRowView) ?? [], [history.data]);
  const rows = useMemo(() => shownRows(saved, live, liveMessages), [saved, live, liveMessages]);
  const leafId = history.data?.current_message_id ?? null;

  const startTurn = useCallback(
    async (turn: TurnStart, execute: (agent: ChatAgent) => Promise<unknown>, seed: AGUIMessage[]) => {
      const agent = agentRef.current;
      if (!agent || runningRef.current) return;
      runningRef.current = true;
      agent.setMessages(seed);
      setLiveMessages(seed);
      updateLive(() => ({
        ...turn,
        continued: turn.continued ?? null,
        assistantId: turn.continued?.id ?? null,
        status: turn.continued ? "running" : "pending",
      }));
      setStatus("submitted");
      setError(null);
      runErrorRef.current = null;
      try {
        await execute(agent);
        setError(runErrorRef.current);
        setStatus(runErrorRef.current ? "error" : "ready");
      } catch (caught) {
        // Never resent automatically (API contract §9).
        setError(toChatError(caught));
        setStatus("error");
      } finally {
        runningRef.current = false;
        const assistantId = liveRef.current?.assistantId;
        if (assistantId) {
          // Load the saved branch through the answer (with its siblings)
          // before dropping the live turn, so the screen never steps back.
          await queryClient.invalidateQueries({
            queryKey: chatKeys.histories(conversationId),
            refetchType: "none",
          });
          try {
            await queryClient.fetchQuery({
              queryKey: chatKeys.history(conversationId, assistantId),
              queryFn: ({ signal }) =>
                getHistory(conversationId, { fromMessageId: assistantId, signal }),
            });
          } catch {
            // The query retries once it is shown.
          }
          setAnchor(assistantId);
        }
        // Without an assistant the request was refused (409, network) and
        // nothing was saved.
        updateLive(() => null);
        await queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      }
    },
    [conversationId, queryClient, updateLive],
  );

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;
      const id = uuidv7();
      await startTurn(
        { kept: saved, question: questionRow(id, trimmed, [id]), questionId: id },
        (agent) =>
          agent.sendMessage({
            parentMessageId: leafId,
            message: { id, text: trimmed, fileIds: [] },
          }),
        [],
      );
    },
    [leafId, saved, startTurn],
  );

  const editMessage = useCallback(
    async (userMessageId: string, text: string) => {
      const trimmed = text.trim();
      const index = saved.findIndex((row) => row.id === userMessageId);
      if (!trimmed || index === -1) return;
      const id = uuidv7();
      await startTurn(
        {
          kept: saved.slice(0, index),
          question: questionRow(id, trimmed, [...saved[index].siblingIds, id]),
          questionId: id,
        },
        (agent) =>
          agent.editMessage({ userMessageId, message: { id, text: trimmed, fileIds: [] } }),
        [],
      );
    },
    [saved, startTurn],
  );

  const regenerate = useCallback(
    async (assistantMessageId: string) => {
      const index = saved.findIndex((row) => row.id === assistantMessageId);
      const question = saved[index - 1];
      if (index < 1 || !question) return;
      await startTurn(
        { kept: saved.slice(0, index), question: null, questionId: question.id },
        (agent) => agent.regenerate({ assistantMessageId }),
        // The answer streams after its question (see shownRows).
        question.content,
      );
    },
    [saved, startTurn],
  );

  const resume = useCallback(
    async (assistantMessageId: string, answers: Record<string, InteractionAnswer>) => {
      const index = saved.findIndex((row) => row.id === assistantMessageId);
      if (index === -1) return;
      await startTurn(
        {
          kept: saved.slice(0, index),
          question: null,
          questionId: "",
          continued: withAnswers(saved[index], answers),
        },
        (agent) => agent.resume({ assistantMessageId, resume: toResumeEntries(answers) }),
        [],
      );
    },
    [saved, startTurn],
  );

  /** One answer; the turn resumes once every waiting question has one. */
  const answerInterrupt = useCallback(
    (assistantMessageId: string, interruptId: string, answer: InteractionAnswer) => {
      const row = saved.find((item) => item.id === assistantMessageId);
      if (!row) return;
      const next = { ...drafts, [interruptId]: answer };
      const waiting = waitingInteractions(row);
      if (waiting.every((item) => item.interrupt_id in next)) {
        setDrafts({});
        void resume(
          assistantMessageId,
          Object.fromEntries(waiting.map((item) => [item.interrupt_id, next[item.interrupt_id]])),
        );
      } else {
        setDrafts(next);
      }
    },
    [drafts, resume, saved],
  );

  const switchBranch = useCallback(
    (messageId: string) => {
      if (runningRef.current) return;
      updateLive(() => null);
      setAnchor(messageId);
    },
    [updateLive],
  );

  const isBusy = status === "submitted" || status === "streaming";
  const lastSaved = saved.at(-1);
  const remoteTurnRunning = !isBusy && isActive(lastSaved);
  // A paused turn holds the chat until it is answered or stopped.
  const waitingForUser = !isBusy && lastSaved?.status === "requires_action";
  const stopTarget = isBusy
    ? live?.assistantId
    : remoteTurnRunning || waitingForUser
      ? lastSaved?.id
      : undefined;

  const stop = useCallback(async () => {
    if (!stopTarget) return;
    try {
      await stopAssistant(conversationId, stopTarget);
    } catch (caught) {
      setError(toChatError(caught));
    }
    // This tab's stream ends by itself; a turn from elsewhere shows on refetch.
    if (!runningRef.current) {
      await queryClient.invalidateQueries({ queryKey: chatKeys.histories(conversationId) });
    }
  }, [conversationId, queryClient, stopTarget]);

  return {
    rows,
    status,
    error,
    isBusy,
    isLoading: history.isLoading,
    isReady: agentReady && history.data !== undefined,
    // A branch switch is loading: the next question must not go to the old leaf.
    isSwitching: history.isPlaceholderData,
    loadError: history.error,
    remoteTurnRunning,
    waitingForUser,
    drafts,
    canStop: !!stopTarget,
    sendMessage,
    editMessage,
    regenerate,
    answerInterrupt,
    switchBranch,
    stop,
  };
}
