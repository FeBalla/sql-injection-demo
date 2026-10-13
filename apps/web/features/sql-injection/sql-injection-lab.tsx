"use client";

import { useState } from "react";

import { ConfirmInsert } from "@/features/sql-injection/components/confirm-insert/confirm-insert";
import { DataCard } from "@/features/sql-injection/components/data/data-card";
import { DatabaseSegmented } from "@/features/sql-injection/components/header/database-segmented";
import { LabHeader } from "@/features/sql-injection/components/header/lab-header";
import { InsertForm } from "@/features/sql-injection/components/insert-form/insert-form";
import { MobileActionBar } from "@/features/sql-injection/components/insert-form/mobile-action-bar";
import { QueryPreview } from "@/features/sql-injection/components/query-preview/query-preview";
import { ResultAlert } from "@/features/sql-injection/components/shared/result-alert";
import { useCustomers } from "@/features/sql-injection/hooks/use-customers";
import { useDatabases } from "@/features/sql-injection/hooks/use-databases";
import { useInsertFlow } from "@/features/sql-injection/hooks/use-insert-flow";
import { useResetDemo } from "@/features/sql-injection/hooks/use-reset-demo";
import { useResultMessage } from "@/features/sql-injection/hooks/use-result-message";
import { useStatementPreview } from "@/features/sql-injection/hooks/use-statement-preview";
import {
  APOSTROPHE_EDGE_CASE,
  EMPTY_ROW,
} from "@/features/sql-injection/model/quick-fill-presets";
import type {
  CustomerRow,
  Db,
  StatementRequest,
} from "@/features/sql-injection/model/types";

/** The SQL injection lab: data, insert form, live preview and confirmation. */
export function SqlInjectionLab() {
  const [db, setDb] = useState<Db>("postgres");
  const [row, setRow] = useState<CustomerRow>(APOSTROPHE_EDGE_CASE);
  const [parameterized, setParameterized] = useState(false);
  const request: StatementRequest = { row, parameterized };

  const { databases, refresh: refreshDatabases } = useDatabases();
  const database = databases.find((item) => item.id === db) ?? databases[0];
  const customers = useCustomers(db);
  const preview = useStatementPreview(db, request);
  const { message, alertRef, showMessage, dismissMessage } = useResultMessage();

  // Inserts and resets change the table, and can change what the API reports
  // about each database.
  function reloadData() {
    customers.refresh();
    refreshDatabases();
  }

  const insert = useInsertFlow({
    database,
    request,
    showMessage,
    onInserted: customers.showLastPage,
    onSettled: reloadData,
  });
  const reset = useResetDemo({
    db,
    table: database.table,
    showMessage,
    onReset: () => customers.setPage(1),
    onSettled: reloadData,
  });

  // The database stays fixed while an insert is being reviewed or run.
  const dbLocked = insert.inProgress;

  function changeDb(next: Db) {
    if (next === db || dbLocked) return;
    setDb(next);
    customers.setPage(1);
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <LabHeader
        databases={databases}
        db={db}
        onDbChange={changeDb}
        dbDisabled={dbLocked}
        onReset={reset.reset}
        resetting={reset.resetting}
      />

      <main className="mx-auto flex w-full max-w-[1440px] flex-1 flex-col gap-4 p-4 md:flex-row md:flex-wrap md:items-start md:gap-6 md:px-8 md:pt-7 md:pb-12">
        <DatabaseSegmented
          databases={databases}
          value={db}
          onChange={changeDb}
          disabled={dbLocked}
          className="md:hidden"
        />

        {/* Wide: left column (Data, Insert). Narrow: its children join the
            main column so the order becomes Insert, Preview, Data. */}
        <div className="contents md:flex md:min-w-0 md:flex-[999_1_560px] md:flex-col md:gap-6">
          <div className="order-3 md:order-none">
            <div ref={alertRef} aria-live="polite" className="scroll-my-4">
              {message && (
                <div className="mb-4 md:mb-6">
                  <ResultAlert message={message} onDismiss={dismissMessage} />
                </div>
              )}
            </div>
            <DataCard
              table={database.table}
              rows={customers.rows}
              total={customers.total}
              page={customers.page}
              pageCount={customers.pageCount}
              initialLoading={customers.initialLoading}
              error={customers.error}
              onPageChange={customers.setPage}
            />
          </div>

          <InsertForm
            className="order-1 md:order-none"
            row={row}
            onRowChange={setRow}
            table={database.table}
            onReview={insert.review}
            reviewing={insert.reviewing}
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
        reviewing={insert.reviewing}
      />

      <ConfirmInsert
        open={insert.confirmOpen}
        onOpenChange={insert.setConfirmOpen}
        statement={insert.pending?.statement ?? null}
        database={insert.pending?.database ?? database}
        running={insert.running}
        onConfirm={insert.run}
      />
    </div>
  );
}
