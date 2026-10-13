import { ArrowRight, LoaderCircle } from "lucide-react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { EMPTY_ROW } from "@/features/sql-injection/model/quick-fill-presets";
import {
  COLUMNS,
  type CustomerRow,
} from "@/features/sql-injection/model/types";
import { cn } from "@/lib/utils";

import { FormField } from "./form-field";
import { QuickFillBar } from "./quick-fill-bar";

/** Lets the mobile action bar, outside the form, submit it. */
export const INSERT_FORM_ID = "insert-form";

type InsertFormProps = {
  row: CustomerRow;
  onRowChange: (row: CustomerRow) => void;
  /** Table of the selected database, used by the malicious example. */
  table: string;
  onReview: () => void;
  reviewing: boolean;
  className?: string;
};

/** "Insert a row": quick fill presets, the four fields and the actions. */
export function InsertForm({
  row,
  onRowChange,
  table,
  onReview,
  reviewing,
  className,
}: InsertFormProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onReview();
  }

  return (
    <section
      aria-labelledby="insert-title"
      className={cn(
        "flex flex-col gap-4 rounded-2xl border bg-card p-4 md:gap-[18px] md:rounded-xl md:p-5",
        className,
      )}
    >
      <h2 id="insert-title" className="text-base font-semibold">
        Insert a row
      </h2>

      <QuickFillBar row={row} table={table} onFill={onRowChange} />

      <form
        id={INSERT_FORM_ID}
        noValidate
        onSubmit={handleSubmit}
        className="flex flex-col gap-[18px]"
      >
        <div className="grid grid-cols-2 gap-3 md:grid-cols-[repeat(auto-fit,minmax(min(180px,100%),1fr))] md:gap-3.5">
          {COLUMNS.map((column) => (
            <FormField
              key={column}
              column={column}
              value={row[column]}
              onChange={(value) => onRowChange({ ...row, [column]: value })}
            />
          ))}
        </div>

        {/* Narrow screens use the sticky MobileActionBar instead. */}
        <div className="hidden justify-end gap-2.5 md:flex">
          <Button
            type="button"
            variant="outline"
            onClick={() => onRowChange(EMPTY_ROW)}
            className="h-11 rounded-md border-input bg-card px-5 text-sm hover:bg-surface-subtle"
          >
            Clear
          </Button>
          <Button
            type="submit"
            disabled={reviewing}
            className="h-11 gap-2 rounded-md px-[22px] text-sm hover:bg-primary/85"
          >
            Review &amp; insert
            {reviewing ? (
              <LoaderCircle aria-hidden="true" className="animate-spin" />
            ) : (
              <ArrowRight aria-hidden="true" />
            )}
          </Button>
        </div>
      </form>
    </section>
  );
}
