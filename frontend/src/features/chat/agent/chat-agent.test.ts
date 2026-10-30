import { afterEach, describe, expect, it, vi } from "vitest";
import { clearAccessToken, setAccessToken } from "@/lib/auth/session";
import { ASSISTANT_EVENT, ChatAgent } from "./chat-agent";

function sse(events: object[]): Response {
  const body = events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join("");
  return new Response(body, { headers: { "Content-Type": "text/event-stream" } });
}

const turn = (assistantId: string) => [
  { type: "RUN_STARTED", threadId: "c1", runId: "server-run" },
  {
    type: "CUSTOM",
    name: ASSISTANT_EVENT,
    value: { conversationId: "c1", userMessageId: "u1", assistantMessageId: assistantId, status: "running" },
  },
  { type: "TEXT_MESSAGE_START", messageId: "m1", role: "assistant" },
  { type: "TEXT_MESSAGE_CONTENT", messageId: "m1", delta: "Chào" },
  { type: "TEXT_MESSAGE_END", messageId: "m1" },
  {
    type: "CUSTOM",
    name: ASSISTANT_EVENT,
    value: { conversationId: "c1", userMessageId: "u1", assistantMessageId: assistantId, status: "completed" },
  },
  { type: "RUN_FINISHED", threadId: "c1", runId: "server-run" },
];

afterEach(() => {
  vi.unstubAllGlobals();
  clearAccessToken();
});

describe("ChatAgent", () => {
  it("sends only the new message as the application DTO", async () => {
    setAccessToken("t1");
    const fetchMock = vi.fn(async () => sse(turn("a1")));
    vi.stubGlobal("fetch", fetchMock);
    const agent = new ChatAgent({
      conversationId: "c1",
      initialMessages: [{ id: "old", role: "user", content: "trước" }],
    });

    await agent.sendMessage({
      parentMessageId: "a0",
      message: { id: "u1", text: "Xin chào", fileIds: [] },
    });

    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/api/v1/conversations/c1/messages");
    expect(JSON.parse(String(init.body))).toEqual({
      parent_message_id: "a0",
      message: { id: "u1", text: "Xin chào", file_ids: [] },
    });
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer t1");
    expect(agent.messages.map((m) => [m.id, m.role, m.content])).toEqual([
      ["old", "user", "trước"],
      ["u1", "user", "Xin chào"],
      ["m1", "assistant", "Chào"],
    ]);
  });

  it("reports the SQL assistant row through the custom event", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => sse(turn("a9"))));
    const agent = new ChatAgent({ conversationId: "c1" });
    const statuses: string[] = [];
    agent.subscribe({
      onCustomEvent: ({ event }) => {
        if (event.name === ASSISTANT_EVENT) {
          const value = event.value as { assistantMessageId: string; status: string };
          statuses.push(`${value.assistantMessageId}:${value.status}`);
        }
      },
    });
    await agent.sendMessage({ parentMessageId: null, message: { id: "u1", text: "x", fileIds: [] } });
    expect(statuses).toEqual(["a9:running", "a9:completed"]);
  });

  it("surfaces an API error before the stream with its status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        Response.json({ error: { code: "assistant_active" } }, { status: 409 }),
      ),
    );
    const agent = new ChatAgent({ conversationId: "c1" });
    agent.subscribe({ onRunFailed: () => undefined });
    await expect(
      agent.sendMessage({ parentMessageId: null, message: { id: "u1", text: "x", fileIds: [] } }),
    ).rejects.toMatchObject({ status: 409, payload: { error: { code: "assistant_active" } } });
  });
});
