import type {
  Segment,
  SegmentKind,
} from "@/features/sql-injection/model/types";
import { cn } from "@/lib/utils";

const SEGMENT_CLASS: Record<SegmentKind, string> = {
  keyword: "text-code-keyword",
  plain: "text-code-foreground",
  string: "text-code-string",
  param: "font-medium text-code-param",
  // Text typed by the user, still inside its string literal.
  input:
    "rounded-[3px] bg-code-input-bg text-code-string shadow-[inset_0_-1px_0_var(--color-code-input-line)]",
  // Text typed by the user that escaped its string literal and became SQL.
  escaped:
    "rounded-[3px] bg-code-escaped-bg text-code-escaped shadow-[inset_0_-1px_0_var(--color-code-escaped-line)]",
};

type CodeLinesProps = {
  lines: Segment[][];
  /** Width of the line-number gutter on wide screens. */
  gutter?: "panel" | "dialog";
  className?: string;
};

/** SQL rendered line by line with line numbers and per-segment highlighting. */
export function CodeLines({
  lines,
  gutter = "panel",
  className,
}: CodeLinesProps) {
  return (
    <div
      translate="no"
      className={cn(
        "w-max min-w-full font-mono text-[13px] leading-[22px] md:text-[13.5px] md:leading-6",
        className,
      )}
    >
      {lines.map((segments, index) => (
        <div key={index} className="flex whitespace-pre">
          <span
            aria-hidden="true"
            className={cn(
              "w-8 flex-none pr-3 text-right text-code-line-number select-none",
              gutter === "panel" ? "md:w-11 md:pr-4" : "md:w-10 md:pr-4",
            )}
          >
            {index + 1}
          </span>
          <span className="pr-4">
            {segments.map((segment, i) => (
              <span key={i} className={SEGMENT_CLASS[segment.kind]}>
                {segment.text}
              </span>
            ))}
          </span>
        </div>
      ))}
    </div>
  );
}
