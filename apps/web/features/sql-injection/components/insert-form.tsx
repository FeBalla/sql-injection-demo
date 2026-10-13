import { ArrowRight, Dice3, LoaderCircle, TriangleAlert } from "lucide-react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

import { COLUMNS, type Column, type CustomerRow } from "../types";
import { ApostropheIcon } from "./icons";
import { QuickFillChip } from "./quick-fill-chip";

export const INSERT_FORM_ID = "insert-form";

type InsertFormProps = {
  row: CustomerRow;
  onRowChange: (row: CustomerRow) => void;
  onRandom: () => void;
  onApostrophe: () => void;
  onMalicious: () => void;
  onClear: () => void;
  onReview: () => void;
  reviewing: boolean;
  className?: string;
};

export function InsertForm({
  row,
  onRowChange,
  onRandom,
  onApostrophe,
  onMalicious,
  onClear,
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

      <div className="flex flex-col gap-2">
        <span
          id="quick-fill-label"
          className="text-xs font-medium tracking-[.04em] text-muted-foreground uppercase"
        >
          Quick fill
        </span>
        <div
          role="group"
          aria-labelledby="quick-fill-label"
          className="-mx-4 flex gap-2 overflow-x-auto px-4 py-0.5 md:mx-0 md:flex-wrap md:overflow-visible md:px-0"
        >
          <QuickFillChip onClick={onRandom}>
            <Dice3 aria-hidden="true" />
            Random valid row
          </QuickFillChip>
          <QuickFillChip tone="info" onClick={onApostrophe}>
            <ApostropheIcon />
            Apostrophe edge case
          </QuickFillChip>
          <QuickFillChip tone="warning" onClick={onMalicious}>
            <TriangleAlert aria-hidden="true" />
            Malicious example
          </QuickFillChip>
        </div>
      </div>

      <form
        id={INSERT_FORM_ID}
        noValidate
        onSubmit={handleSubmit}
        className="flex flex-col gap-[18px]"
      >
        <div className="grid grid-cols-2 gap-3 md:grid-cols-[repeat(auto-fit,minmax(min(180px,100%),1fr))] md:gap-3.5">
          {COLUMNS.map((column) => (
            <Field
              key={column}
              column={column}
              value={row[column]}
              onChange={(value) => onRowChange({ ...row, [column]: value })}
            />
          ))}
        </div>

        <div className="hidden justify-end gap-2.5 md:flex">
          <Button
            type="button"
            variant="outline"
            onClick={onClear}
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

function Field({
  column,
  value,
  onChange,
}: {
  column: Column;
  value: string;
  onChange: (value: string) => void;
}) {
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
