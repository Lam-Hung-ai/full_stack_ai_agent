import {
  Sidebar,
  SidebarFooter,
  SidebarHeader,
  SidebarInset,
  SidebarProvider,
  SidebarRail,
  SidebarTrigger,
} from "@/components/ui/sidebar";

/**
 * Application frame: a full-height sidebar that folds to an icon rail
 * (Ctrl+B) and becomes a sheet on phones, beside the main area.
 */
export function AppShell({
  brand,
  sidebar,
  footer,
  children,
}: {
  brand: React.ReactNode;
  sidebar?: React.ReactNode;
  footer?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider className="h-dvh min-h-0">
      <Sidebar collapsible="icon">
        <SidebarHeader className="flex-row items-center gap-1">
          <SidebarTrigger aria-label="Ẩn hoặc hiện thanh bên" />
          <span className="truncate font-serif font-semibold text-lg group-data-[collapsible=icon]:hidden">
            {brand}
          </span>
        </SidebarHeader>
        <div
          className="flex min-h-0 flex-1 flex-col overflow-y-auto group-data-[collapsible=icon]:overflow-hidden"
          data-sidebar="content"
        >
          {sidebar}
        </div>
        {footer && <SidebarFooter>{footer}</SidebarFooter>}
        <SidebarRail />
      </Sidebar>
      <SidebarInset className="min-h-0 min-w-0 overflow-hidden">{children}</SidebarInset>
    </SidebarProvider>
  );
}
