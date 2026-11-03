"use client";

import { SidebarTrigger, useSidebar } from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";

/**
 * Top bar of a page inside the app frame. On phones it carries the button
 * that opens the sidebar; with no content it shows only there.
 */
export function PageHeader({
  children,
  end,
  className,
}: {
  children?: React.ReactNode;
  end?: React.ReactNode;
  className?: string;
}) {
  const { isMobile } = useSidebar();
  if (!children && !end && !isMobile) return null;
  return (
    <header className={cn("flex h-12 shrink-0 items-center gap-2 px-3", className)}>
      {isMobile && <SidebarTrigger aria-label="Mở thanh bên" />}
      <div className="flex min-w-0 flex-1 items-center">{children}</div>
      {end && <div className="flex shrink-0 items-center gap-1">{end}</div>}
    </header>
  );
}
