import { Database, RotateCcw } from "lucide-react";

import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

import type { DatabaseInfo, Db } from "../types";
import { DatabaseSelect } from "./database-picker";

type LabHeaderProps = {
  databases: DatabaseInfo[];
  db: Db;
  onDbChange: (db: Db) => void;
  onReset: () => void;
  resetting: boolean;
};

export function LabHeader({
  databases,
  db,
  onDbChange,
  onReset,
  resetting,
}: LabHeaderProps) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b bg-card px-4 py-3 md:gap-4 md:px-8 md:py-[18px]">
      <div className="flex items-center gap-2.5 md:gap-3">
        <div className="flex size-[30px] items-center justify-center rounded-md bg-primary text-background md:size-8">
          <Database aria-hidden="true" className="size-4 md:size-[18px]" />
        </div>
        <div className="flex flex-col">
          <h1 className="text-base font-semibold">Injection Lab</h1>
          <p className="hidden text-[13px] text-muted-foreground md:block">
            String concatenation vs parameterized queries
          </p>
        </div>
      </div>

      <div className="hidden flex-wrap items-center gap-3 md:flex">
        <Label
          htmlFor="database"
          className="text-[13px] font-normal text-muted-foreground"
        >
          Database
        </Label>
        <DatabaseSelect
          id="database"
          databases={databases}
          value={db}
          onChange={onDbChange}
        />
        <button
          type="button"
          onClick={onReset}
          disabled={resetting}
          className="inline-flex h-10 items-center gap-1.5 rounded-md border border-input bg-card px-3 text-[13px] font-medium transition-colors hover:border-input-hover focus-visible:outline-2 focus-visible:outline-offset-2 disabled:opacity-60"
        >
          <ResetIcon spinning={resetting} className="size-4" />
          Reset demo data
        </button>
      </div>

      <button
        type="button"
        onClick={onReset}
        disabled={resetting}
        aria-label="Reset demo data"
        className="flex size-11 items-center justify-center rounded-lg border border-input bg-card focus-visible:outline-2 focus-visible:outline-offset-2 disabled:opacity-60 md:hidden"
      >
        <ResetIcon spinning={resetting} className="size-[18px]" />
      </button>
    </header>
  );
}

function ResetIcon({
  spinning,
  className,
}: {
  spinning: boolean;
  className?: string;
}) {
  return (
    <RotateCcw
      aria-hidden="true"
      className={cn(
        className,
        spinning && "animate-spin [animation-direction:reverse]",
      )}
    />
  );
}
