// Types mirroring the SQL injection API (apps/api/app/modules/sql_injection/schemas.py).

export type Db = "postgres" | "bigquery";

export type Column = "name" | "email" | "country" | "plan";

export const COLUMNS: readonly Column[] = ["name", "email", "country", "plan"];

/** The four editable values of a customer row. */
export type CustomerRow = Record<Column, string>;

export type Customer = CustomerRow & { id: number };

export type CustomerPage = {
  rows: Customer[];
  total: number;
  page: number;
  page_size: number;
};

export type DatabaseInfo = {
  id: Db;
  label: string;
  /** Table reference shown in the UI and used in the SQL, e.g. "public.customers". */
  table: string;
  available: boolean;
  reason: string | null;
};

export type ResetResult = { total: number };

export type StatementRequest = {
  row: CustomerRow;
  parameterized: boolean;
};

export type SegmentKind =
  "keyword" | "plain" | "string" | "param" | "input" | "escaped";

export type Segment = { text: string; kind: SegmentKind };

export type BoundParam = {
  placeholder: string;
  column: Column;
  type: "text" | "STRING";
  value: string;
};

export type StatementPreview = {
  database: Db;
  parameterized: boolean;
  /** Exact text sent to the database. */
  sql: string;
  lines: Segment[][];
  params: BoundParam[];
  /** Statements the database will actually see. */
  statement_count: number;
  /** Fields whose value escapes its string literal. */
  escaped_fields: Column[];
};

export type InsertResult = {
  ok: boolean;
  statement: StatementPreview;
  rows_affected: number | null;
  total_rows: number | null;
  error: string | null;
};
