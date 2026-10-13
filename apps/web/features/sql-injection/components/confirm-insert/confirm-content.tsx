import type { StatementPreview } from "@/features/sql-injection/model/types";

import { BoundParamsTable } from "./bound-params-table";
import { ConfirmNote } from "./confirm-note";
import { StatementBlock } from "./statement-block";

/** The statement, its bound parameters (if any) and what they mean. */
export function ConfirmContent({
  statement,
  compact,
}: {
  statement: StatementPreview;
  /** Bottom sheet layout: shorter labels, fewer columns. */
  compact: boolean;
}) {
  return (
    <>
      <StatementBlock statement={statement} compact={compact} />
      {statement.parameterized && statement.params.length > 0 && (
        <BoundParamsTable statement={statement} compact={compact} />
      )}
      <ConfirmNote statement={statement} />
    </>
  );
}
