import { COLUMNS, type Customer } from "@/features/sql-injection/model/types";

type CustomersTableProps = {
  rows: Customer[];
  /** Shown in a single row instead of `rows`. */
  emptyMessage: string | null;
};

/** The rows as a data table (wide screens). */
export function CustomersTable({ rows, emptyMessage }: CustomersTableProps) {
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
