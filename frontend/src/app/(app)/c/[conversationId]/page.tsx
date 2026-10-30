import { ConversationScreen } from "@/features/chat";

export const instant = false;

export default async function Page({ params }: PageProps<"/c/[conversationId]">) {
  const { conversationId } = await params;
  // Keyed so switching chats starts from a fresh agent and history.
  return <ConversationScreen conversationId={conversationId} key={conversationId} />;
}
