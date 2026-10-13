import type { DatabaseInfo, Db } from "@/features/sql-injection/model/types";
import { cn } from "@/lib/utils";

type DatabaseSegmentedProps = {
  databases: DatabaseInfo[];
  value: Db;
  onChange: (db: Db) => void;
  disabled?: boolean;
  className?: string;
};

/** Segmented control (narrow screens). */
export function DatabaseSegmented({
  databases,
  value,
  onChange,
  disabled = false,
  className,
}: DatabaseSegmentedProps) {
  return (
    <div
      role="group"
      aria-label="Database"
      className={cn("flex gap-1 rounded-xl bg-segment p-1", className)}
    >
      {databases.map((database) => {
        const selected = database.id === value;
        return (
          <button
            key={database.id}
            type="button"
            aria-pressed={selected}
            aria-disabled={!database.available}
            disabled={disabled && !selected}
            title={database.reason ?? undefined}
            onClick={() => database.available && onChange(database.id)}
            className={cn(
              "flex h-11 flex-1 flex-col items-center justify-center rounded-md text-sm leading-tight font-medium focus-visible:outline-2 focus-visible:outline-offset-1 disabled:cursor-default disabled:opacity-60",
              selected && "bg-card",
              !database.available && "cursor-not-allowed text-muted-foreground",
            )}
          >
            {database.label}
            {!database.available && (
              <span className="text-[11px] font-normal">unavailable</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
