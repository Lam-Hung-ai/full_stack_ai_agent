/** A list response of the API: one page of `data` and where it stands. */
export type Page<T> = {
  data: T[];
  pagination: { page: number; has_next_page: boolean };
};

/** Largest `page_size` the backend accepts (MAX_PAGE_SIZE). */
export const MAX_PAGE_SIZE = 100;

/**
 * Every page of a list that is small in practice (an organization's members,
 * a user's workspaces), merged into one response so no item is cut off.
 */
export async function allPages<T, R extends Page<T>>(
  fetchPage: (page: number) => Promise<R>,
): Promise<R> {
  const first = await fetchPage(1);
  const data = [...first.data];
  let last = first;
  while (last.pagination.has_next_page) {
    last = await fetchPage(last.pagination.page + 1);
    data.push(...last.data);
  }
  return { ...first, data };
}
