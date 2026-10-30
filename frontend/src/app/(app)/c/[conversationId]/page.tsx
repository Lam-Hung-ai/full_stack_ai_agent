import { ConversationScreen } from "@/features/chat";

export const instant = false;

export default async function Page({ params, searchParams }: PageProps<"/c/[conversationId]">) {
  const { conversationId } = await params;
  // `m`: open the branch through this message (a search result).
  const { m } = await searchParams;
  const messageId = typeof m === "string" ? m : null;
  // Keyed so switching chats (or results) starts from a fresh agent and history.
  return (
    <ConversationScreen
      conversationId={conversationId}
      key={`${conversationId}:${messageId ?? ""}`}
      messageId={messageId}
    />
  );
}
