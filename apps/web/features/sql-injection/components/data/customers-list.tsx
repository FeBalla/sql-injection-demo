import type { ReactNode } from "react";

import type { Customer } from "@/features/sql-injection/model/types";

type CustomersListProps = {
  rows: Customer[];
  /** Shown instead of `rows`. */
  emptyMessage: string | null;
};

/** The rows as a list: name and email, country and plan as tags (narrow screens). */
export function CustomersList({ rows, emptyMessage }: CustomersListProps) {
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
