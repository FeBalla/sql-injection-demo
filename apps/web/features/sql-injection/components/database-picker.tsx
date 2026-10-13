import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

import type { DatabaseInfo, Db } from "../types";

type PickerProps = {
  databases: DatabaseInfo[];
  value: Db;
  onChange: (db: Db) => void;
  disabled?: boolean;
};

/** Header dropdown (wide screens). Unavailable databases are disabled. */
export function DatabaseSelect({
  id,
  databases,
  value,
  onChange,
  disabled = false,
}: PickerProps & { id: string }) {
  return (
    <Select
      value={value}
      onValueChange={(next) => onChange(next as Db)}
      disabled={disabled}
    >
      <SelectTrigger
        id={id}
        className="h-10 min-w-[124px] gap-3 rounded-md border-input bg-card px-3 text-sm font-medium data-[size=default]:h-10 [&_svg]:text-foreground"
      >
        <SelectValue />
      </SelectTrigger>
      <SelectContent position="popper" align="end">
        {databases.map((database) => (
          <SelectItem
            key={database.id}
            value={database.id}
            disabled={!database.available}
            title={database.reason ?? undefined}
            className="py-2 text-sm data-disabled:pointer-events-auto"
          >
            {database.label}
            {!database.available && (
              <span className="text-xs text-muted-foreground">unavailable</span>
            )}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

/** Segmented control (narrow screens). */
export function DatabaseSegmented({
  databases,
  value,
  onChange,
  disabled = false,
  className,
}: PickerProps & { className?: string }) {
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
