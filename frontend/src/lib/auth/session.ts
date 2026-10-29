/**
 * Access token of the current session, held in memory only (QD-12).
 *
 * The refresh token lives in an HttpOnly cookie that scripts cannot read; a
 * page reload starts from `POST /api/v1/auth/session`. Never persisted to
 * localStorage: a token there is readable by any injected script.
 */
let accessToken: string | null = null;
const expiredListeners = new Set<() => void>();

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string): void {
  accessToken = token;
}

export function clearAccessToken(): void {
  accessToken = null;
}

/** Called when the session can no longer be refreshed; returns an unsubscribe. */
export function onSessionExpired(listener: () => void): () => void {
  expiredListeners.add(listener);
  return () => {
    expiredListeners.delete(listener);
  };
}

export function notifySessionExpired(): void {
  clearAccessToken();
  for (const listener of expiredListeners) listener();
}
