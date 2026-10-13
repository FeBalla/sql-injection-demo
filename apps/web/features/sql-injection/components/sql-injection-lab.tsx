"use client";

import { useRef, useState } from "react";

import {
  insertCustomer,
  PAGE_SIZE,
  previewStatement,
  resetCustomers,
} from "../api";
import { useCustomers } from "../hooks/use-customers";
import { useDatabases } from "../hooks/use-databases";
import { useStatementPreview } from "../hooks/use-statement-preview";
import {
  APOSTROPHE_EDGE_CASE,
  EMPTY_ROW,
  maliciousExample,
  randomValidRow,
} from "../quick-fill";
import { plural } from "../statement-copy";
import type {
  Customer,
  CustomerRow,
  DatabaseInfo,
  Db,
  InsertResult,
  StatementPreview,
  StatementRequest,
} from "../types";
import { ConfirmInsert } from "./confirm-insert";
import { DataCard } from "./data-card";
import { DatabaseSegmented } from "./database-picker";
import { InsertForm } from "./insert-form";
import { LabHeader } from "./lab-header";
import { MobileActionBar } from "./mobile-action-bar";
import { QueryPreview } from "./query-preview";
import { ResultAlert, type ResultMessage } from "./result-alert";

type PendingInsert = { request: StatementRequest; statement: StatementPreview };

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function insertMessage(result: InsertResult, table: string): ResultMessage {
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

/** The SQL injection lab: data, insert form, live preview and confirmation. */
export function SqlInjectionLab() {
  const [db, setDb] = useState<Db>("postgres");
  const [row, setRow] = useState<CustomerRow>(APOSTROPHE_EDGE_CASE);
  const [parameterized, setParameterized] = useState(false);
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Customer | null>(null);
  const [message, setMessage] = useState<ResultMessage | null>(null);
  const [pending, setPending] = useState<PendingInsert | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [running, setRunning] = useState(false);
  const [resetting, setResetting] = useState(false);
  const alertRef = useRef<HTMLDivElement>(null);

  const { databases, refresh: refreshDatabases } = useDatabases();
  const database: DatabaseInfo =
    databases.find((item) => item.id === db) ?? databases[0];
  const customers = useCustomers(db, page);
  const preview = useStatementPreview(db, { row, parameterized });

  function showMessage(next: ResultMessage) {
    setMessage(next);
    // On narrow screens the alert can be off-screen; bring it into view.
    requestAnimationFrame(() =>
      alertRef.current?.scrollIntoView({
        block: "nearest",
        behavior: "smooth",
      }),
    );
  }

  function changeDb(next: Db) {
    if (next === db) return;
    setDb(next);
    setPage(1);
    setSelected(null);
  }

  function toggleSelected(customer: Customer) {
    setSelected((current) => (current?.id === customer.id ? null : customer));
  }

  async function review() {
    const request: StatementRequest = { row, parameterized };
    setReviewing(true);
    try {
      const statement = await previewStatement(db, request);
      setPending({ request, statement });
      setConfirmOpen(true);
    } catch (error) {
      showMessage({
        tone: "error",
        title: "Could not build the statement",
        detail: errorText(error),
      });
    } finally {
      setReviewing(false);
    }
  }

  async function runInsert() {
    if (!pending) return;
    setRunning(true);
    try {
      const result = await insertCustomer(db, pending.request);
      showMessage(insertMessage(result, database.table));
      if (result.ok && result.total_rows !== null) {
        // Jump to the last page so the new row (if any) is visible.
        setPage(Math.max(1, Math.ceil(result.total_rows / PAGE_SIZE)));
      }
      if (result.statement.statement_count > 1) setSelected(null);
    } catch (error) {
      showMessage({
        tone: "error",
        title: "The insert request failed",
        detail: errorText(error),
      });
    } finally {
      setRunning(false);
      setConfirmOpen(false);
      customers.refresh();
      refreshDatabases();
    }
  }

  async function resetData() {
    setResetting(true);
    try {
      const { total } = await resetCustomers(db);
      setSelected(null);
      setPage(1);
      showMessage({
        tone: "info",
        title: "Demo data reset",
        body: `${database.table} is back to its ${plural(total, "seed row")}.`,
      });
    } catch (error) {
      showMessage({
        tone: "error",
        title: "Could not reset the demo data",
        detail: errorText(error),
      });
    } finally {
      setResetting(false);
      customers.refresh();
      refreshDatabases();
    }
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <LabHeader
        databases={databases}
        db={db}
        onDbChange={changeDb}
        onReset={resetData}
        resetting={resetting}
      />

      <main className="mx-auto flex w-full max-w-[1440px] flex-1 flex-col gap-4 p-4 md:flex-row md:flex-wrap md:items-start md:gap-6 md:px-8 md:pt-7 md:pb-12">
        <DatabaseSegmented
          databases={databases}
          value={db}
          onChange={changeDb}
          className="md:hidden"
        />

        {/* Wide: left column (Data, Insert). Narrow: its children join the
            main column so the order becomes Insert, Preview, Data. */}
        <div className="contents md:flex md:min-w-0 md:flex-[999_1_560px] md:flex-col md:gap-6">
          <div className="order-3 md:order-none">
            <div ref={alertRef} aria-live="polite" className="scroll-my-4">
              {message && (
                <div className="mb-4 md:mb-6">
                  <ResultAlert
                    message={message}
                    onDismiss={() => setMessage(null)}
                  />
                </div>
              )}
            </div>
            <DataCard
              table={database.table}
              rows={customers.rows}
              total={customers.total}
              page={page}
              pageCount={customers.pageCount}
              initialLoading={customers.initialLoading}
              error={customers.error}
              selectedId={selected?.id ?? null}
              onSelect={toggleSelected}
              onPageChange={setPage}
            />
          </div>

          <InsertForm
            className="order-1 md:order-none"
            row={row}
            onRowChange={setRow}
            canCopySelected={selected !== null}
            onRandom={() => setRow(randomValidRow(row))}
            onCopySelected={() => {
              if (!selected) return;
              const { name, email, country, plan } = selected;
              setRow({ name, email, country, plan });
            }}
            onApostrophe={() => setRow(APOSTROPHE_EDGE_CASE)}
            onMalicious={() => setRow(maliciousExample(database.table))}
            onClear={() => setRow(EMPTY_ROW)}
            onReview={review}
            reviewing={reviewing}
          />
        </div>

        <QueryPreview
          className="order-2 md:order-none md:min-w-0 md:flex-[1_1_460px]"
          preview={preview.preview}
          error={preview.error}
          parameterized={parameterized}
          onParameterizedChange={setParameterized}
        />
      </main>

      <MobileActionBar
        onClear={() => setRow(EMPTY_ROW)}
        reviewing={reviewing}
      />

      <ConfirmInsert
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        statement={pending?.statement ?? null}
        database={database}
        running={running}
        onConfirm={runInsert}
      />
    </div>
  );
}
