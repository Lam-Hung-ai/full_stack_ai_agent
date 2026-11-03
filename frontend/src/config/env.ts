/**
 * Public runtime configuration, read and validated in one place.
 *
 * `NEXT_PUBLIC_API_URL` is the FastAPI origin. Empty means same origin: the
 * browser calls `/api/v1/...` on the Next.js host, which keeps the refresh
 * cookie first-party (SameSite=Strict) when a rewrite or proxy forwards it.
 */
export const env = {
  apiUrl: (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/+$/, ""),
} as const;
