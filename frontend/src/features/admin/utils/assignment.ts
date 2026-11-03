/** Edits of a purpose's ordered model list: the first answers, the rest are fallbacks. */

export function addModel(ids: readonly string[], id: string): string[] {
  return ids.includes(id) ? [...ids] : [...ids, id];
}

export function removeModel(ids: readonly string[], id: string): string[] {
  return ids.filter((item) => item !== id);
}

/** Move the model at `index` one place up (-1) or down (+1); out of range stays. */
export function moveModel(ids: readonly string[], index: number, step: -1 | 1): string[] {
  const target = index + step;
  if (index < 0 || index >= ids.length || target < 0 || target >= ids.length) return [...ids];
  const next = [...ids];
  [next[index], next[target]] = [next[target], next[index]];
  return next;
}
