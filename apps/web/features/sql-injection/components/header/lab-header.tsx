import { Database } from "lucide-react";

import { Label } from "@/components/ui/label";
import type { DatabaseInfo, Db } from "@/features/sql-injection/model/types";

import { DatabaseSelect } from "./database-select";
import { ResetButton, ResetIconButton } from "./reset-button";

type LabHeaderProps = {
  databases: DatabaseInfo[];
  db: Db;
  onDbChange: (db: Db) => void;
  dbDisabled?: boolean;
  onReset: () => void;
  resetting: boolean;
};

/** Title bar. Wide screens also get the database picker and a labeled reset. */
export function LabHeader({
  databases,
  db,
  onDbChange,
  dbDisabled = false,
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
          disabled={dbDisabled}
        />
        <ResetButton onReset={onReset} resetting={resetting} />
      </div>

      <ResetIconButton onReset={onReset} resetting={resetting} />
    </header>
  );
}
