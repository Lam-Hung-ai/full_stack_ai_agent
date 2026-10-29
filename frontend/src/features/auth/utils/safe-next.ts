/**
 * Where to go after login. Only same-site paths are accepted, so a crafted
 * `?next=https://evil.example` or `//evil.example` cannot redirect off-site.
 */
export function safeNext(next: string | null | undefined, fallback = "/"): string {
  if (!next || !next.startsWith("/") || next.startsWith("//") || next.includes("\\")) {
    return fallback;
  }
  return next;
}
