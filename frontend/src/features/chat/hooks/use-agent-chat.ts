"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { HttpAgent, type Message as AGUIMessage } from "@ag-ui/client";
import type { ChatStatus } from "ai";

export function useAgentChat() {
  const agentRef = useRef<HttpAgent | null>(null);
  const [messages, setMessages] = useState<AGUIMessage[]>([]);
  const [status, setStatus] = useState<ChatStatus>("ready");
  const hadErrorRef = useRef(false);

  // A long reasoning stream can fire onMessagesChanged hundreds of times within
  // a single browser frame. Coalescing them to one setMessages per animation
  // frame keeps React from reconciling a state that gets overwritten before the
  // browser ever paints it — no data is lost, only the number of renders drops.
  const pendingMessagesRef = useRef<AGUIMessage[] | null>(null);
  const frameRef = useRef<number | null>(null);
  const scheduleMessages = useCallback((updated: AGUIMessage[]) => {
    pendingMessagesRef.current = updated;
    if (frameRef.current !== null) return;
    frameRef.current = requestAnimationFrame(() => {
      frameRef.current = null;
      if (pendingMessagesRef.current) setMessages(pendingMessagesRef.current);
    });
  }, []);

  // HttpAgent's constructor touches crypto.randomUUID(); constructing it during
  // render would make Next.js's prerender treat that as an unstable value, so
  // it's created after mount. It's kept in a ref (not state) so mounting it
  // doesn't need a synchronous setState call inside the effect.
  useEffect(() => {
    const instance = new HttpAgent({ url: "/api/agent" });
    agentRef.current = instance;

    const { unsubscribe } = instance.subscribe({
      onMessagesChanged: ({ messages: updated }) => scheduleMessages([...updated]),
      onTextMessageStartEvent: () => setStatus("streaming"),
      onRunErrorEvent: ({ event }) => {
        hadErrorRef.current = true;
        console.error("Agent run error:", event.message);
      },
    });

    return () => {
      unsubscribe();
      agentRef.current = null;
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
    };
  }, [scheduleMessages]);

  const sendMessage = useCallback(
    async (text: string) => {
      const agent = agentRef.current;
      const trimmed = text.trim();
      if (!agent || !trimmed || status === "submitted" || status === "streaming") return;

      agent.addMessage({ id: crypto.randomUUID(), role: "user", content: trimmed });
      setMessages([...agent.messages]);
      setStatus("submitted");
      hadErrorRef.current = false;

      try {
        await agent.runAgent();
        setStatus(hadErrorRef.current ? "error" : "ready");
      } catch (error) {
        console.error(error);
        setStatus("error");
      }
    },
    [status],
  );

  return { messages, status, sendMessage };
}
