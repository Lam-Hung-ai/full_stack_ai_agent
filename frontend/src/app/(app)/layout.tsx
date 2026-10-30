import { AppShell } from "@/components/layout/app-shell";
import { AuthGate, UserMenu } from "@/features/auth";
import { ConversationSidebar, ExportChatsMenuItem } from "@/features/chat";
import { OrganizationMenuItems } from "@/features/organizations";
import { WorkspaceSwitcher } from "@/features/workspaces";

export default function AppLayout({ children }: LayoutProps<"/">) {
  return (
    <AuthGate>
      <AppShell
        end={<UserMenu />}
        sidebar={<ConversationSidebar />}
        start={
          <WorkspaceSwitcher
            actions={
              <>
                <OrganizationMenuItems />
                <ExportChatsMenuItem />
              </>
            }
          />
        }
      >
        {children}
      </AppShell>
    </AuthGate>
  );
}
