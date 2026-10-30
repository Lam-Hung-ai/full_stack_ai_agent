/** File name from a `Content-Disposition` header, if it gives one: the
 * UTF-8 `filename*` first, the plain `filename` otherwise. */
export function attachmentName(header: string | null, fallback: string): string {
  const encoded = header?.match(/filename\*=UTF-8''([^;]+)/i);
  if (encoded) return decodeURIComponent(encoded[1].trim());
  const plain = header?.match(/filename="?([^";]+)"?/i);
  return plain ? plain[1] : fallback;
}

/** Hand a downloaded body to the browser as a file to save. */
export function saveBlob(blob: Blob, name: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  // Give the browser a moment to start the download before freeing it.
  setTimeout(() => URL.revokeObjectURL(url), 1_000);
}
