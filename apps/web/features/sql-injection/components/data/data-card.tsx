import type { Customer } from "@/features/sql-injection/model/types";
import { cn } from "@/lib/utils";

import { CustomersList } from "./customers-list";
import { CustomersTable } from "./customers-table";
import { Pagination } from "./pagination";

type DataCardProps = {
  table: string;
  rows: Customer[];
  total: number;
  page: number;
  pageCount: number;
  initialLoading: boolean;
  error: string | null;
  onPageChange: (page: number) => void;
  className?: string;
};

/** The demo table: a data table on wide screens, a list on narrow ones. */
export function DataCard({
  table,
  rows,
  total,
  page,
  pageCount,
  initialLoading,
  error,
  onPageChange,
  className,
}: DataCardProps) {
  const emptyMessage = emptyMessageFor({ rows, total, initialLoading, error });

  return (
    <section
      aria-labelledby="data-title"
      className={cn(
        "overflow-hidden rounded-2xl border bg-card md:rounded-xl",
        className,
      )}
    >
      <div className="flex items-baseline justify-between gap-2.5 px-4 py-3.5 md:justify-start md:px-5 md:py-4">
        <h2 id="data-title" className="text-base font-semibold">
          Data
        </h2>
        <span className="truncate font-mono text-xs text-muted-foreground md:text-[13px]">
          {table}
        </span>
      </div>

      <CustomersTable rows={rows} emptyMessage={emptyMessage} />
      <CustomersList rows={rows} emptyMessage={emptyMessage} />

      <Pagination
        page={page}
        pageCount={pageCount}
        total={total}
        onPageChange={onPageChange}
      />
    </section>
  );
}

type LoadState = Pick<
  DataCardProps,
  "rows" | "total" | "initialLoading" | "error"
>;

/** What to show instead of rows, or null when there are rows to show. */
function emptyMessageFor({
  rows,
  total,
  initialLoading,
  error,
}: LoadState): string | null {
  if (error) return `Could not load the table: ${error}`;
  // Rows can be briefly missing while a page past the end is being clamped.
  if (initialLoading || (rows.length === 0 && total > 0)) {
    return "Loading rows…";
  }
  if (rows.length === 0) {
    return "The table is empty. Reset demo data to restore the seed rows.";
  }
  return null;
}
