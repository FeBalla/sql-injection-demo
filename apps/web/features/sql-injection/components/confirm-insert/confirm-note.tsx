import { TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";

import { joinList } from "@/features/sql-injection/copy/format";
import { quotedPlaceholders } from "@/features/sql-injection/copy/status-copy";
import type { StatementPreview } from "@/features/sql-injection/model/types";

/** What will happen to the input: stored as data, or run as SQL. */
export function ConfirmNote({ statement }: { statement: StatementPreview }) {
  if (statement.parameterized) {
    const quoted = quotedPlaceholders(statement);
    if (quoted.length === 0) {
      return <Note>Values are sent separately and stored as data.</Note>;
    }
    const quoteCount = statement.params.reduce(
      (total, param) => total + param.value.split("'").length - 1,
      0,
    );
    const many = quoteCount > 1;
    return (
      <Note>
        {many ? "The quotes" : "The apostrophe"} in{" "}
        {quoted.map((placeholder, i) => (
          <span key={placeholder}>
            {i > 0 && (i === quoted.length - 1 ? " and " : ", ")}
            <span className="font-mono text-foreground">{placeholder}</span>
          </span>
        ))}{" "}
        {many ? "are" : "is"} stored as data.{" "}
        {many ? "They never become" : "It never becomes"} part of the SQL.
      </Note>
    );
  }

  const escaped = statement.escaped_fields;
  if (escaped.length === 0) {
    return <Note>Values are pasted into the SQL text as they are.</Note>;
  }
  const count = statement.statement_count;
  return (
    <div className="flex items-start gap-2.5 rounded-lg border border-warning-border bg-warning-soft px-3.5 py-3 text-[13px] leading-normal text-warning-strong">
      <TriangleAlert aria-hidden="true" className="mt-px size-4 flex-none" />
      <p>
        Input in <span className="font-mono">{joinList(escaped)}</span> escapes
        its string literal and becomes SQL.{" "}
        {count > 1
          ? `The database will receive ${count} statements in one request.`
          : "The database receives 1 statement with that text as part of its code."}
      </p>
    </div>
  );
}

function Note({ children }: { children: ReactNode }) {
  return (
    <p className="text-[13px] leading-normal text-muted-foreground">
      {children}
    </p>
  );
}
