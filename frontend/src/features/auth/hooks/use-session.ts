"use client";

import { useQuery } from "@tanstack/react-query";
import { setAccessToken } from "@/lib/auth/session";
import { startSession } from "../api/auth-api";

export const sessionKey = ["session"] as const;

/**
 * The session opened from the refresh cookie on page load. Fetched once:
 * every call rotates the cookie, so it is never refetched in the background.
 */
export function useSession() {
  return useQuery({
    queryKey: sessionKey,
    // No abort signal: the server rotates the refresh cookie as soon as the
    // request arrives, so an aborted call would lose the new cookie and the
    // next attempt would present an already rotated one.
    queryFn: async () => {
      const session = await startSession();
      setAccessToken(session.access_token);
      return session;
    },
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false,
    refetchOnReconnect: false,
  });
}
