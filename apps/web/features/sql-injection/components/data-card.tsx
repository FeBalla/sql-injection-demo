import { ChevronLeft, ChevronRight } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

import { PAGE_SIZE } from "../api";
import { COLUMNS, type Customer } from "../types";

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
  const shownPage = Math.min(page, pageCount);
  const first = total === 0 ? 0 : (shownPage - 1) * PAGE_SIZE + 1;
  const last = Math.min(shownPage * PAGE_SIZE, total);
  const range = total === 0 ? "No rows" : `${first}–${last} of ${total}`;

  let emptyMessage: ReactNode = null;
  if (error) emptyMessage = `Could not load the table: ${error}`;
  // Rows can be briefly missing while a page past the end is being clamped.
  else if (initialLoading || (rows.length === 0 && total > 0))
    emptyMessage = "Loading rows…";
  else if (rows.length === 0)
    emptyMessage =
      "The table is empty. Reset demo data to restore the seed rows.";

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

      <DataTable rows={rows} emptyMessage={emptyMessage} />
      <DataList rows={rows} emptyMessage={emptyMessage} />

      <nav
        aria-label="Table pages"
        className="flex items-center justify-between border-t border-divider py-1 pr-2 pl-4 md:border-t-0 md:py-2 md:pr-3 md:pl-5"
      >
        <span className="text-[13px] text-muted-foreground" aria-live="polite">
          <span className="hidden md:inline">{total > 0 && "Rows "}</span>
          {range}
        </span>
        <div className="flex gap-1">
          <PageButton
            label="Previous page"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            <ChevronLeft aria-hidden="true" />
          </PageButton>
          <PageButton
            label="Next page"
            disabled={page >= pageCount}
            onClick={() => onPageChange(page + 1)}
          >
            <ChevronRight aria-hidden="true" />
          </PageButton>
        </div>
      </nav>
    </section>
  );
}

type RowsProps = {
  rows: Customer[];
  emptyMessage: ReactNode;
};

function DataTable({ rows, emptyMessage }: RowsProps) {
  return (
    <div className="hidden overflow-x-auto md:block">
      <table className="w-full border-collapse text-sm">
        <caption className="sr-only">Rows of the demo table</caption>
        <thead>
          <tr>
            {["id", ...COLUMNS].map((header) => (
              <th
                key={header}
                scope="col"
                className="border-b bg-surface-subtle px-3.5 py-2.5 text-left text-xs font-medium tracking-[.04em] text-muted-foreground uppercase"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {emptyMessage ? (
            <tr>
              <td
                colSpan={COLUMNS.length + 1}
                className="border-b border-divider px-3.5 py-6 text-center text-muted-foreground"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((customer) => (
              <tr key={customer.id}>
                <td className="border-b border-divider px-3.5 py-[11px] font-mono whitespace-nowrap">
                  {customer.id}
                </td>
                {COLUMNS.map((column) => (
                  <td
                    key={column}
                    className="max-w-[16rem] truncate border-b border-divider px-3.5 py-[11px] whitespace-nowrap"
                    title={customer[column]}
                  >
                    {customer[column]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function DataList({ rows, emptyMessage }: RowsProps) {
  if (emptyMessage) {
    return (
      <p className="border-t border-divider px-4 py-6 text-center text-sm text-muted-foreground md:hidden">
        {emptyMessage}
      </p>
    );
  }
  return (
    <ul className="md:hidden" aria-label="Rows of the demo table">
      {rows.map((customer) => (
        <li
          key={customer.id}
          className="flex min-h-11 items-center justify-between gap-3 border-t border-divider px-4 py-3"
        >
          <span className="flex min-w-0 flex-col gap-0.5">
            <span className="truncate text-[15px] font-medium">
              {customer.name}
            </span>
            <span className="truncate text-[13px] text-muted-foreground">
              {customer.email}
            </span>
          </span>
          <span className="flex flex-none gap-1.5">
            <Tag>{customer.country}</Tag>
            <Tag>{customer.plan}</Tag>
          </span>
        </li>
      ))}
    </ul>
  );
}

function Tag({ children }: { children: ReactNode }) {
  return (
    <span className="max-w-24 truncate rounded-sm bg-tag px-2 py-[3px] font-mono text-xs font-medium text-tag-foreground">
      {children}
    </span>
  );
}

function PageButton({
  label,
  disabled,
  onClick,
  children,
}: {
  label: string;
  disabled: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className="flex size-11 items-center justify-center rounded-md text-foreground transition-colors hover:bg-surface-subtle focus-visible:outline-2 disabled:cursor-default disabled:text-muted-foreground disabled:opacity-60 disabled:hover:bg-transparent [&_svg]:size-[18px]"
    >
      {children}
    </button>
  );
}
