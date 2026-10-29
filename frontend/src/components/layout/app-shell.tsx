/** Application frame: a top bar with start/end slots above a full-height main area. */
export function AppShell({
  start,
  end,
  children,
}: {
  start?: React.ReactNode;
  end?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-dvh flex-col">
      <header className="flex h-12 shrink-0 items-center justify-between gap-2 border-b px-4">
        <div className="flex min-w-0 items-center gap-2">{start}</div>
        <div className="flex items-center gap-2">{end}</div>
      </header>
      <main className="min-h-0 flex-1">{children}</main>
    </div>
  );
}
