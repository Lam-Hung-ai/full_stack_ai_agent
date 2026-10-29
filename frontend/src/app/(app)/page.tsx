import { ChatScreen } from "@/features/chat";

// Rendered only inside AuthGate once the session is known, so there is no
// static shell to validate for instant navigation.
export const instant = false;

export default function Page() {
  return <ChatScreen />;
}
