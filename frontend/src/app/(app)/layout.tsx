import { AppShell } from "@/components/layout/app-shell";
import { ThemeMenu } from "@/components/layout/theme-menu";
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
            <ThemeMenu />
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
