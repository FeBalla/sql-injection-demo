// One function per endpoint of the SQL injection API.

import type {
  CustomerPage,
  DatabaseInfo,
  Db,
  InsertResult,
  ResetResult,
  StatementPreview,
  StatementRequest,
} from "@/features/sql-injection/model/types";

import { request } from "./client";

/** Rows per page of the demo table. */
export const PAGE_SIZE = 5;

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
