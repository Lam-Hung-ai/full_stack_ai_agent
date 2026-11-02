import { AppShell } from "@/components/layout/app-shell";
import { AuthGate, UserMenu } from "@/features/auth";
import { ConversationSidebar, ExportChatsMenuItem } from "@/features/chat";
import { OrganizationMenuItems } from "@/features/organizations";
import { CurrentWorkspaceName, WorkspaceMenu } from "@/features/workspaces";

export default function AppLayout({ children }: LayoutProps<"/">) {
  return (
    <AuthGate>
      <AppShell
        brand="Agent Chat"
        footer={
          <UserMenu subtitle={<CurrentWorkspaceName />}>
            <WorkspaceMenu
              actions={
                <>
                  <OrganizationMenuItems />
                  <ExportChatsMenuItem />
                </>
              }
            />
          </UserMenu>
        }
        sidebar={<ConversationSidebar />}
      >
        {children}
      </AppShell>
    </AuthGate>
  );
}
