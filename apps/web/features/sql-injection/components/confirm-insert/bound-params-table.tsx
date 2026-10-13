import type { StatementPreview } from "@/features/sql-injection/model/types";
import { cn } from "@/lib/utils";

/** Placeholder, column, type and value of each bound parameter. */
export function BoundParamsTable({
  statement,
  compact,
}: {
  statement: StatementPreview;
  /** Bottom sheet layout: no type column, header row visually hidden. */
  compact: boolean;
}) {
  const cell = compact ? "px-3 py-2.5" : "px-3.5 py-2.5";
  return (
    <div className="overflow-hidden rounded-xl border md:rounded-lg">
      <table className="w-full table-fixed font-mono text-[13px]">
        <caption
          className={cn(
            "bg-surface-subtle text-left font-sans text-xs tracking-[.04em] text-muted-foreground uppercase",
            compact ? "px-3 py-2.5" : "px-3.5 py-2.5",
          )}
        >
          Bound parameters
        </caption>
        <colgroup>
          <col className={compact ? "w-[52px]" : "w-[70px]"} />
          <col className={compact ? "w-[82px]" : "w-[132px]"} />
          {!compact && <col className="w-[76px]" />}
          <col />
        </colgroup>
        <thead className={cn(compact ? "sr-only" : "bg-surface-subtle")}>
          <tr className="border-t border-divider text-left text-xs text-muted-foreground">
            <th scope="col" className={cn("font-normal", cell)}>
              param
            </th>
            <th scope="col" className={cn("font-normal", cell)}>
              column
            </th>
            {!compact && (
              <th scope="col" className={cn("font-normal", cell)}>
                type
              </th>
            )}
            <th scope="col" className={cn("font-normal", cell)}>
              value
            </th>
          </tr>
        </thead>
        <tbody>
          {statement.params.map((param) => (
            <tr key={param.placeholder} className="border-t border-divider">
              <td className={cn("font-medium text-param", cell)}>
                {param.placeholder}
              </td>
              <td className={cn(compact && "text-muted-foreground", cell)}>
                {param.column}
              </td>
              {!compact && (
                <td className={cn("text-muted-foreground", cell)}>
                  {param.type}
                </td>
              )}
              <td className={cn("[overflow-wrap:anywhere]", cell)}>
                {param.value}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
