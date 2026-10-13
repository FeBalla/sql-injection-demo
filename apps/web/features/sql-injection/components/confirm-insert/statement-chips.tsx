import { Shield, TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";

import { plural } from "@/features/sql-injection/copy/format";
import type {
  DatabaseInfo,
  StatementPreview,
} from "@/features/sql-injection/model/types";
import { cn } from "@/lib/utils";

/** Database, statement count and mode, as chips. */
export function StatementChips({
  statement,
  database,
  compact = false,
}: {
  statement: StatementPreview;
  database: DatabaseInfo;
  /** Bottom sheet layout: database label without the table. */
  compact?: boolean;
}) {
  const count = statement.statement_count;
  return (
    <div className="flex flex-wrap gap-1.5 md:gap-2">
      <Chip>
        {compact ? database.label : `${database.label} · ${database.table}`}
      </Chip>
      <Chip tone={count > 1 ? "warning" : "neutral"}>
        {plural(count, "statement")}
      </Chip>
      {statement.parameterized ? (
        <Chip tone="info">
          <Shield aria-hidden="true" />
          Parameterized
        </Chip>
      ) : (
        <Chip tone="warning">
          <TriangleAlert aria-hidden="true" />
          Concatenated
        </Chip>
      )}
    </div>
  );
}

function Chip({
  tone = "neutral",
  children,
}: {
  tone?: "neutral" | "info" | "warning";
  children: ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-[26px] items-center gap-1.5 rounded-sm px-2.5 font-mono text-xs [&_svg]:size-[13px] [&_svg]:stroke-[2.2]",
        tone === "neutral" && "bg-tag text-tag-foreground",
        tone === "info" && "bg-info-soft text-info-strong",
        tone === "warning" && "bg-warning-soft text-warning-strong",
      )}
    >
      {children}
    </span>
  );
}
