// Wording of the alert shown above the table after a review, insert or reset.

import type { InsertResult } from "@/features/sql-injection/model/types";

import { plural } from "./format";

export type ResultMessage = {
  tone: "success" | "info" | "warning" | "error";
  title: string;
  body?: string;
  /** Raw database error, shown in mono. */
  detail?: string;
};

/** Outcome of an insert the API answered, ok or rejected by the database. */
export function insertResultMessage(
  result: InsertResult,
  table: string,
): ResultMessage {
  const count = result.statement.statement_count;
  const totalRows = result.total_rows;

  if (!result.ok) {
    return {
      tone: "error",
      title: "The database rejected the statement",
      body:
        totalRows === null
          ? undefined
          : `${table} still has ${plural(totalRows, "row")}.`,
      detail: result.error ?? "Unknown database error.",
    };
  }

  const ran = `${plural(count, "statement")} ran`;
  const affected =
    result.rows_affected === null
      ? ""
      : ` and affected ${plural(result.rows_affected, "row")}`;
  const total =
    totalRows === null ? "" : ` ${table} now has ${plural(totalRows, "row")}.`;
  return {
    tone: count > 1 ? "warning" : "success",
    title: count > 1 ? `All ${count} statements ran` : "Row inserted",
    body: `${ran}${affected}.${total}`,
  };
}

export function insertRequestFailedMessage(error: unknown): ResultMessage {
  return {
    tone: "error",
    title: "The insert request failed",
    detail: errorText(error),
  };
}

export function reviewFailedMessage(error: unknown): ResultMessage {
  return {
    tone: "error",
    title: "Could not build the statement",
    detail: errorText(error),
  };
}

export function resetDoneMessage(total: number, table: string): ResultMessage {
  return {
    tone: "info",
    title: "Demo data reset",
    body: `${table} is back to its ${plural(total, "seed row")}.`,
  };
}

export function resetFailedMessage(error: unknown): ResultMessage {
  return {
    tone: "error",
    title: "Could not reset the demo data",
    detail: errorText(error),
  };
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
