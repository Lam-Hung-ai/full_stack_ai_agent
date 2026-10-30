"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Message as AGUIMessage } from "@ag-ui/client";
import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ChatStatus } from "ai";
import { v7 as uuidv7 } from "uuid";
import type { ApiError } from "@/lib/api";
import { ASSISTANT_EVENT, ChatAgent, type AssistantEventValue } from "../agent/chat-agent";
import { getHistory, stopAssistant } from "../api/conversations-api";
import type { ChatFile } from "../api/files-api";
import type { ComposerDraft } from "../components/chat-composer";
import type { LiveTurn, RowView } from "../types/chat.types";
import { attachedFiles, questionContent, withText } from "../utils/files";
import { isActive, shownRows, toChatError, toRowView } from "../utils/history";
import {
  type InteractionAnswer,
  toResumeEntries,
  waitingInteractions,
  withAnswers,
} from "../utils/interactions";
import { chatKeys } from "./use-conversations";

const ACTIVE_POLL_MS = 2_000;
/** When the sidebar looks again for the name a new chat gets (C01). */
const TITLE_REFRESH_MS = [3_000, 10_000];

type TurnStart = Pick<LiveTurn, "kept" | "question" | "questionId"> & {
  continued?: RowView;
};

function questionRow(
  id: string,
  text: string,
  siblingIds: string[],
  files: readonly ChatFile[] = [],
): RowView {
  return {
    id,
    role: "user",
    status: "completed",
    content: [{ id, role: "user", content: questionContent(text, files) } as AGUIMessage],
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
 * over that branch until the saved branch holds its answer. A turn started
 * elsewhere (another tab, before a reload) is followed through `attach`;
 * when its live data is gone the history is polled until it is saved.
 * Leaving the conversation drops the stream; the turn goes on (QD-23).
 */
export function useConversationChat(conversationId: string, initialAnchor: string | null = null) {
  const queryClient = useQueryClient();
  const [anchor, setAnchor] = useState<string | null>(initialAnchor);
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
  // Told once whether the server took the turn's question (an assistant row
  // exists), so the composer clears only then.
  const acceptRef = useRef<((accepted: boolean) => void) | null>(null);
  const settleAccepted = useCallback((accepted: boolean) => {
    acceptRef.current?.(accepted);
    acceptRef.current = null;
  }, []);

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
        settleAccepted(true);
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
  }, [conversationId, scheduleMessages, settleAccepted, updateLive]);

  const saved = useMemo(() => history.data?.data.map(toRowView) ?? [], [history.data]);
  const rows = useMemo(() => shownRows(saved, live, liveMessages), [saved, live, liveMessages]);
  const leafId = history.data?.current_message_id ?? null;

  const startTurn = useCallback(
    async (
      turn: TurnStart,
      execute: (agent: ChatAgent) => Promise<unknown>,
      seed: AGUIMessage[],
      onAccepted?: (accepted: boolean) => void,
    ) => {
      const agent = agentRef.current;
      if (!agent || runningRef.current) {
        onAccepted?.(false);
        return;
      }
      runningRef.current = true;
      acceptRef.current = onAccepted ?? null;
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
        settleAccepted(Boolean(assistantId));
        updateLive(() => null);
        await queryClient.invalidateQueries({ queryKey: ["workspaces"] });
        if (assistantId && turn.kept.length === 0 && !turn.continued) {
          // A new chat is named in the background (C01) and the name may
          // land after the answer: look again a little later.
          for (const delay of TITLE_REFRESH_MS) {
            setTimeout(
              () => void queryClient.invalidateQueries({ queryKey: ["workspaces"] }),
              delay,
            );
          }
        }
      }
    },
    [conversationId, queryClient, settleAccepted, updateLive],
  );

  /** Resolves once the server took the question (true) or refused it. */
  const sendMessage = useCallback(
    ({ text, files }: ComposerDraft) =>
      new Promise<boolean>((resolve) => {
        const trimmed = text.trim();
        if (!trimmed && files.length === 0) {
          resolve(false);
          return;
        }
        const id = uuidv7();
        void startTurn(
          { kept: saved, question: questionRow(id, trimmed, [id], files), questionId: id },
          (agent) =>
            agent.sendMessage({
              parentMessageId: leafId,
              message: { id, text: trimmed, fileIds: files.map((file) => file.id) },
            }),
          [],
          resolve,
        );
      }),
    [leafId, saved, startTurn],
  );

  const editMessage = useCallback(
    async (userMessageId: string, text: string) => {
      const trimmed = text.trim();
      const index = saved.findIndex((row) => row.id === userMessageId);
      if (!trimmed || index === -1) return;
      const id = uuidv7();
      // The new version keeps the files of the one it replaces.
      const original = saved[index].content.find((message) => message.role === "user");
      const files = attachedFiles(original);
      const question: RowView = {
        ...questionRow(id, trimmed, [...saved[index].siblingIds, id]),
        content: [{ id, role: "user", content: withText(original, trimmed) } as AGUIMessage],
      };
      await startTurn(
        { kept: saved.slice(0, index), question, questionId: id },
        (agent) =>
          agent.editMessage({
            userMessageId,
            message: { id, text: trimmed, fileIds: files.map((file) => file.id) },
          }),
        [],
      );
    },
    [saved, startTurn],
  );

  // Follow a turn that runs without this tab, once per assistant row.
  const attachedRef = useRef<string | null>(null);
  const attach = useCallback(
    async (row: RowView) => {
      const index = saved.findIndex((item) => item.id === row.id);
      await startTurn(
        { kept: saved.slice(0, index), question: null, questionId: "", continued: row },
        (agent) => agent.attach(),
        [],
      );
    },
    [saved, startTurn],
  );
  useEffect(() => {
    const last = saved.at(-1);
    if (!agentReady || runningRef.current || !last || !isActive(last)) return;
    if (attachedRef.current === last.id) return;
    attachedRef.current = last.id;
    // Deferred: starting the stream sets state.
    queueMicrotask(() => void attach(last));
  }, [agentReady, attach, saved]);

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
