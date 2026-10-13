import { Dice3, TriangleAlert } from "lucide-react";

import { ApostropheIcon } from "@/features/sql-injection/components/shared/icons";
import {
  APOSTROPHE_EDGE_CASE,
  maliciousExample,
  randomValidRow,
} from "@/features/sql-injection/model/quick-fill-presets";
import type { CustomerRow } from "@/features/sql-injection/model/types";

import { QuickFillChip } from "./quick-fill-chip";

type QuickFillBarProps = {
  /** Current form values; "Random valid row" picks a different one. */
  row: CustomerRow;
  /** Table of the selected database, targeted by the malicious example. */
  table: string;
  onFill: (row: CustomerRow) => void;
};

/** "Quick fill" presets: a random valid row, the apostrophe and the attack. */
export function QuickFillBar({ row, table, onFill }: QuickFillBarProps) {
  return (
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
        <QuickFillChip onClick={() => onFill(randomValidRow(row))}>
          <Dice3 aria-hidden="true" />
          Random valid row
        </QuickFillChip>
        <QuickFillChip tone="info" onClick={() => onFill(APOSTROPHE_EDGE_CASE)}>
          <ApostropheIcon />
          Apostrophe edge case
        </QuickFillChip>
        <QuickFillChip
          tone="warning"
          onClick={() => onFill(maliciousExample(table))}
        >
          <TriangleAlert aria-hidden="true" />
          Malicious example
        </QuickFillChip>
      </div>
    </div>
  );
}
