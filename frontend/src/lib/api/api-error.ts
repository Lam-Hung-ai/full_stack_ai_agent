/**
 * Error returned by FastAPI in the shared contract
 * `{"error": {code, message?, details?, request_id?}}`.
 *
 * `status` 0 marks a failure before any response (network, CORS, abort).
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown;
  readonly requestId: string | null;

  constructor(
    status: number,
    code: string,
    options: { message?: string; details?: unknown; requestId?: string | null } = {},
  ) {
    super(options.message ?? code);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = options.details;
    this.requestId = options.requestId ?? null;
  }
}

type ErrorBody = {
  error?: { code?: unknown; message?: unknown; details?: unknown; request_id?: unknown };
};

/** Turn a non-2xx response into an `ApiError`, tolerating non-JSON bodies. */
export async function toApiError(response: Response): Promise<ApiError> {
  let body: ErrorBody | null = null;
  try {
    body = (await response.json()) as ErrorBody;
  } catch {
    // Proxies and crashes can answer with HTML or nothing at all.
  }
  const error = body?.error;
  return new ApiError(
    response.status,
    typeof error?.code === "string" ? error.code : "http_error",
    {
      message: typeof error?.message === "string" ? error.message : undefined,
      details: error?.details,
      requestId:
        typeof error?.request_id === "string"
          ? error.request_id
          : response.headers.get("x-request-id"),
    },
  );
}
