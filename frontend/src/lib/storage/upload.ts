/**
 * PUT a file to a presigned URL, after hr-ai (QD-14). Not the API client: the
 * object store gets no cookie or bearer token, only the headers that were
 * signed (AGENTS §10).
 */
type PresignedUploadTarget = {
  url: string;
  method: string;
  headers: Record<string, string>;
};

export class StorageUploadError extends Error {
  constructor(
    public readonly code: "storage_upload_unreachable" | "storage_upload_rejected",
    public readonly status?: number,
  ) {
    super(code);
    this.name = "StorageUploadError";
  }
}

export async function uploadPresignedFile(
  file: File,
  target: PresignedUploadTarget,
  signal?: AbortSignal,
) {
  let response: Response;
  try {
    response = await fetch(target.url, {
      method: target.method,
      headers: target.headers,
      body: file,
      credentials: "omit",
      cache: "no-store",
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new StorageUploadError("storage_upload_unreachable");
  }
  if (!response.ok) {
    throw new StorageUploadError("storage_upload_rejected", response.status);
  }
}
