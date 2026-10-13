import type {
  CustomerPage,
  DatabaseInfo,
  Db,
  InsertResult,
  ResetResult,
  StatementPreview,
  StatementRequest,
} from "./types";

const BASE = "/api/sql-injection";

export const PAGE_SIZE = 5;

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
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

export function listDatabases(): Promise<DatabaseInfo[]> {
  return request("/databases");
}

export function listCustomers(
  db: Db,
  page: number,
  signal?: AbortSignal,
): Promise<CustomerPage> {
  return request(`/${db}/customers?page=${page}&page_size=${PAGE_SIZE}`, {
    signal,
  });
}

export function resetCustomers(db: Db): Promise<ResetResult> {
  return request(`/${db}/reset`, { method: "POST" });
}

export function previewStatement(
  db: Db,
  body: StatementRequest,
  signal?: AbortSignal,
): Promise<StatementPreview> {
  return request(`/${db}/preview`, {
    method: "POST",
    body: JSON.stringify(body),
    signal,
  });
}

export function insertCustomer(
  db: Db,
  body: StatementRequest,
): Promise<InsertResult> {
  return request(`/${db}/insert`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
