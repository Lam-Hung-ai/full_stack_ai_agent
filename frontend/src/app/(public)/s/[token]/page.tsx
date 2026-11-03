import { SharedChatScreen } from "@/features/shares";

// Client-only screen: nothing static to validate for instant navigation.
export const instant = false;

export default async function SharedChatPage({ params }: PageProps<"/s/[token]">) {
  const { token } = await params;
  return <SharedChatScreen token={token} />;
}
