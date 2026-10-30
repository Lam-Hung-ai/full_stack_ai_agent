/** Matching as the backend's `search_key` does: no case, no accents (C09). */

/** One character folded to one character, so positions stay aligned. */
function fold(char: string): string {
  if (char === "đ" || char === "Đ") return "d";
  const base = char.normalize("NFD").replace(/\p{M}/gu, "");
  return (base || char)[0].toLowerCase();
}

function folded(text: string): string {
  return Array.from(text, fold).join("");
}

export const MIN_SEARCH_LENGTH = 2;

/** The query as sent, or null while it is too short to search. */
export function searchTerm(input: string): string | null {
  const term = input.split(/\s+/).filter(Boolean).join(" ");
  return term.length >= MIN_SEARCH_LENGTH ? term : null;
}

export type SnippetPart = { text: string; match: boolean };

/** `text` split around every place `query` occurs, accents ignored. */
export function highlight(text: string, query: string): SnippetPart[] {
  const chars = Array.from(text);
  const haystack = folded(text);
  const needle = folded(query.trim());
  if (!needle) return [{ text, match: false }];
  const parts: SnippetPart[] = [];
  let from = 0;
  for (let at = haystack.indexOf(needle); at !== -1; at = haystack.indexOf(needle, from)) {
    if (at > from) parts.push({ text: chars.slice(from, at).join(""), match: false });
    const end = at + Array.from(needle).length;
    parts.push({ text: chars.slice(at, end).join(""), match: true });
    from = end;
  }
  if (from < chars.length) parts.push({ text: chars.slice(from).join(""), match: false });
  return parts;
}
