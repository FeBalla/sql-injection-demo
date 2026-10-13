import { CodeLines } from "@/features/sql-injection/components/shared/code-lines";
import { CopyButton } from "@/features/sql-injection/components/shared/copy-button";
import type { StatementPreview } from "@/features/sql-injection/model/types";
import { useScrollFade } from "@/hooks/use-scroll-fade";

/** The exact SQL that will be sent, with a copy button. */
export function StatementBlock({
  statement,
  compact,
}: {
  statement: StatementPreview;
  /** Bottom sheet layout: shorter heading. */
  compact: boolean;
}) {
  const codeRef = useScrollFade<HTMLDivElement>();
  return (
    <div className="overflow-hidden rounded-xl bg-code md:rounded-lg">
      <div className="flex items-center justify-between border-b border-code-border py-1 pr-1 pl-3 md:py-2 md:pr-2 md:pl-3.5">
        <span className="text-xs tracking-[.04em] text-code-muted uppercase">
          {compact ? "Statement" : "Statement sent to the database"}
        </span>
        <CopyButton
          text={statement.sql}
          className="h-11 px-3 text-[13px] md:h-8 md:px-2.5 md:text-xs"
        />
      </div>
      <div
        ref={codeRef}
        className="max-h-[200px] overflow-auto py-2.5 data-more:[mask-image:linear-gradient(to_right,#000_calc(100%-2rem),transparent)] md:py-3"
      >
        <CodeLines lines={statement.lines} gutter="dialog" />
      </div>
    </div>
  );
}
