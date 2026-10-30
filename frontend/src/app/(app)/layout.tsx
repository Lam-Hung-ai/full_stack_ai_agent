import { AppShell } from "@/components/layout/app-shell";
import { AuthGate, UserMenu } from "@/features/auth";
import { ConversationSidebar } from "@/features/chat";
import { WorkspaceSwitcher } from "@/features/workspaces";

export default function AppLayout({ children }: LayoutProps<"/">) {
  return (
    <AuthGate>
      <AppShell end={<UserMenu />} sidebar={<ConversationSidebar />} start={<WorkspaceSwitcher />}>
        {children}
      </AppShell>
    </AuthGate>
  );
}
