// JSON fetch wrapper for the SQL injection API. Errors become ApiError with
// the API's own message.

const BASE = "/api/sql-injection";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response));
  }
  return (await response.json()) as T;
}

/** FastAPI returns `{detail}`; detail is a string or a list of validation errors. */
async function errorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((item: { msg?: string }) => item.msg ?? "Invalid request")
        .join("; ");
    }
  } catch {
    // Not JSON: fall through to the status text.
  }
  return `Request failed (${response.status} ${response.statusText})`;
}
