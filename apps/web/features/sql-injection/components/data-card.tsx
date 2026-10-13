import { ChevronLeft, ChevronRight } from "lucide-react";
import type { KeyboardEvent, ReactNode } from "react";

import { cn } from "@/lib/utils";

import { PAGE_SIZE } from "../api";
import type { Customer } from "../types";

type DataCardProps = {
  table: string;
  rows: Customer[];
  total: number;
  page: number;
  pageCount: number;
  initialLoading: boolean;
  error: string | null;
  selectedId: number | null;
  onSelect: (customer: Customer) => void;
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
  selectedId,
  onSelect,
  onPageChange,
  className,
}: DataCardProps) {
  const first = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const last = Math.min(page * PAGE_SIZE, total);
  const range = total === 0 ? "No rows" : `${first}–${last} of ${total}`;

  let emptyMessage: ReactNode = null;
  if (error) emptyMessage = `Could not load the table: ${error}`;
  else if (initialLoading) emptyMessage = "Loading rows…";
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
      <div className="flex items-baseline justify-between gap-3 px-4 py-3.5 md:items-center md:px-5 md:py-4">
        <div className="flex min-w-0 flex-1 items-baseline justify-between gap-2.5 md:flex-none md:justify-start">
          <h2 id="data-title" className="text-base font-semibold">
            Data
          </h2>
          <span className="truncate font-mono text-xs text-muted-foreground md:text-[13px]">
            {table}
          </span>
        </div>
        <span className="hidden text-[13px] text-muted-foreground md:block">
          Click a row to select it
        </span>
      </div>

      <DataTable
        rows={rows}
        selectedId={selectedId}
        onSelect={onSelect}
        emptyMessage={emptyMessage}
      />
      <DataList
        rows={rows}
        selectedId={selectedId}
        onSelect={onSelect}
        emptyMessage={emptyMessage}
      />

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
  selectedId: number | null;
  onSelect: (customer: Customer) => void;
  emptyMessage: ReactNode;
};

const HEADERS = ["id", "name", "email", "country", "plan"] as const;

function DataTable({ rows, selectedId, onSelect, emptyMessage }: RowsProps) {
  function handleKeyDown(
    event: KeyboardEvent<HTMLTableRowElement>,
    customer: Customer,
  ) {
    const row = event.currentTarget;
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect(customer);
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      (row.nextElementSibling as HTMLElement | null)?.focus();
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      (row.previousElementSibling as HTMLElement | null)?.focus();
    }
  }

  return (
    <div className="hidden overflow-x-auto md:block">
      <table className="w-full border-collapse text-sm">
        <caption className="sr-only">
          Rows of the demo table. Press Enter or Space on a row to select it.
        </caption>
        <thead>
          <tr>
            {HEADERS.map((header) => (
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
                colSpan={HEADERS.length}
                className="border-b border-divider px-3.5 py-6 text-center text-muted-foreground"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((customer) => {
              const selected = customer.id === selectedId;
              return (
                <tr
                  key={customer.id}
                  tabIndex={0}
                  aria-selected={selected}
                  onClick={() => onSelect(customer)}
                  onKeyDown={(event) => handleKeyDown(event, customer)}
                  className={cn(
                    "cursor-pointer outline-info transition-colors focus-visible:outline-2 focus-visible:-outline-offset-2",
                    selected ? "bg-info-soft" : "hover:bg-surface-subtle",
                  )}
                >
                  <td className="border-b border-divider px-3.5 py-[11px] font-mono whitespace-nowrap">
                    {customer.id}
                  </td>
                  {(["name", "email", "country", "plan"] as const).map(
                    (column) => (
                      <td
                        key={column}
                        className="max-w-[16rem] truncate border-b border-divider px-3.5 py-[11px] whitespace-nowrap"
                        title={customer[column]}
                      >
                        {customer[column]}
                      </td>
                    ),
                  )}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}

function DataList({ rows, selectedId, onSelect, emptyMessage }: RowsProps) {
  if (emptyMessage) {
    return (
      <p className="border-t border-divider px-4 py-6 text-center text-sm text-muted-foreground md:hidden">
        {emptyMessage}
      </p>
    );
  }
  return (
    <ul className="md:hidden" aria-label="Rows of the demo table">
      {rows.map((customer) => {
        const selected = customer.id === selectedId;
        return (
          <li key={customer.id} className="border-t border-divider">
            <button
              type="button"
              aria-pressed={selected}
              onClick={() => onSelect(customer)}
              className={cn(
                "flex min-h-11 w-full items-center justify-between gap-3 px-4 py-3 text-left outline-info focus-visible:outline-2 focus-visible:-outline-offset-2",
                selected && "bg-info-soft",
              )}
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
            </button>
          </li>
        );
      })}
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
