import { useState } from "react";

import {
  insertCustomer,
  previewStatement,
} from "@/features/sql-injection/api/endpoints";
import {
  insertRequestFailedMessage,
  insertResultMessage,
  reviewFailedMessage,
  type ResultMessage,
} from "@/features/sql-injection/copy/result-messages";
import type {
  DatabaseInfo,
  StatementPreview,
  StatementRequest,
} from "@/features/sql-injection/model/types";

/** What the user is reviewing; the insert runs against this exact database. */
type PendingInsert = {
  database: DatabaseInfo;
  request: StatementRequest;
  statement: StatementPreview;
};

type InsertFlowOptions = {
  /** The selected database; `review` captures it. */
  database: DatabaseInfo;
  /** The form's row and mode; `review` captures them. */
  request: StatementRequest;
  showMessage: (message: ResultMessage) => void;
  /** After a successful insert, with the table's new row count. */
  onInserted: (totalRows: number) => void;
  /** After every insert attempt, to reload what it may have changed. */
  onSettled: () => void;
};

/**
 * Review → confirm → run. `review` asks the API for the exact statement and
 * opens the confirmation; `run` then sends that same request to that same
 * database.
 */
export function useInsertFlow({
  database,
  request,
  showMessage,
  onInserted,
  onSettled,
}: InsertFlowOptions) {
  const [pending, setPending] = useState<PendingInsert | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [running, setRunning] = useState(false);

  async function review() {
    const target = database;
    setReviewing(true);
    try {
      const statement = await previewStatement(target.id, request);
      setPending({ database: target, request, statement });
      setConfirmOpen(true);
    } catch (error) {
      showMessage(reviewFailedMessage(error));
    } finally {
      setReviewing(false);
    }
  }

  async function run() {
    if (!pending) return;
    setRunning(true);
    try {
      const result = await insertCustomer(pending.database.id, pending.request);
      showMessage(insertResultMessage(result, pending.database.table));
      if (result.ok && result.total_rows !== null) {
        onInserted(result.total_rows);
      }
    } catch (error) {
      showMessage(insertRequestFailedMessage(error));
    } finally {
      setRunning(false);
      setConfirmOpen(false);
      onSettled();
    }
  }

  return {
    /** The reviewed insert; kept after the confirmation closes. */
    pending,
    confirmOpen,
    setConfirmOpen,
    reviewing,
    running,
    /** From Review until the confirmation closes. */
    inProgress: reviewing || confirmOpen || running,
    review,
    run,
  };
}
