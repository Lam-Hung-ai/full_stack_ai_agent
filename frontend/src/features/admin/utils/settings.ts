/** Settings passed to init_chat_model, edited as JSON text. */
export type Settings = Record<string, unknown>;

export function formatSettings(settings: Settings): string {
  return Object.keys(settings).length ? JSON.stringify(settings, null, 2) : "";
}

/** The object in `text` (empty means none), or null when it is not one. */
export function parseSettings(text: string): Settings | null {
  if (!text.trim()) return {};
  try {
    const value: unknown = JSON.parse(text);
    return value !== null && typeof value === "object" && !Array.isArray(value)
      ? (value as Settings)
      : null;
  } catch {
    return null;
  }
}
