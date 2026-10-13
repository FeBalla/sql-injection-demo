import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Column } from "@/features/sql-injection/model/types";
import { cn } from "@/lib/utils";

type FormFieldProps = {
  column: Column;
  value: string;
  onChange: (value: string) => void;
};

/** One labeled input per column; name and email span the row on narrow screens. */
export function FormField({ column, value, onChange }: FormFieldProps) {
  const id = `field-${column}`;
  const wide = column === "name" || column === "email";
  return (
    <div
      className={cn(
        "flex min-w-0 flex-col gap-1.5",
        wide && "col-span-2 md:col-span-1",
      )}
    >
      <Label
        htmlFor={id}
        className="font-mono text-xs font-medium text-muted-foreground"
      >
        {column}
      </Label>
      <Input
        id={id}
        name={column}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        maxLength={500}
        autoComplete="off"
        autoCapitalize="off"
        spellCheck={false}
        inputMode={column === "email" ? "email" : "text"}
        className="h-12 rounded-lg border-input bg-card px-3.5 text-base shadow-none focus-visible:border-info focus-visible:ring-0 focus-visible:outline-2 focus-visible:-outline-offset-1 focus-visible:outline-info focus-visible:outline-solid md:h-11 md:rounded-md md:px-3 md:text-sm"
      />
    </div>
  );
}
