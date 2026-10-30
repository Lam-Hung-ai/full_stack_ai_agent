/** Application frame: a top bar, an optional sidebar, a full-height main area. */
export function AppShell({
  start,
  end,
  sidebar,
  children,
}: {
  start?: React.ReactNode;
  end?: React.ReactNode;
  sidebar?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-dvh flex-col">
      <header className="flex h-12 shrink-0 items-center justify-between gap-2 border-b px-4">
        <div className="flex min-w-0 items-center gap-2">{start}</div>
        <div className="flex items-center gap-2">{end}</div>
      </header>
      <div className="flex min-h-0 flex-1">
        {sidebar && (
          <aside className="hidden w-64 shrink-0 border-r md:block">{sidebar}</aside>
        )}
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
