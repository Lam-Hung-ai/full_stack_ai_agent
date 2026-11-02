import { ConversationScreen } from "@/features/chat";

export const instant = false;

export default async function Page({ params, searchParams }: PageProps<"/c/[conversationId]">) {
  const { conversationId } = await params;
  // `t`: open the branch through this turn (a search result).
  const { t } = await searchParams;
  const turnId = typeof t === "string" ? t : null;
  // Keyed so switching chats (or results) starts from a fresh agent and history.
  return (
    <ConversationScreen
      conversationId={conversationId}
      key={`${conversationId}:${turnId ?? ""}`}
      turnId={turnId}
    />
  );
}
