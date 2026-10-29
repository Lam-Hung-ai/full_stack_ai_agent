import { AppShell } from "@/components/layout/app-shell";
import { AuthGate, UserMenu } from "@/features/auth";
import { WorkspaceSwitcher } from "@/features/workspaces";

export default function AppLayout({ children }: LayoutProps<"/">) {
  return (
    <AuthGate>
      <AppShell start={<WorkspaceSwitcher />} end={<UserMenu />}>
        {children}
      </AppShell>
    </AuthGate>
  );
}
