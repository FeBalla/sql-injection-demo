import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { DatabaseInfo, Db } from "@/features/sql-injection/model/types";

type DatabaseSelectProps = {
  id: string;
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
}: DatabaseSelectProps) {
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
