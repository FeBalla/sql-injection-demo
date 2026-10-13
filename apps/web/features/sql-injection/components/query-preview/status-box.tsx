import { ShieldCheck, TriangleAlert } from "lucide-react";

import { statusCopy } from "@/features/sql-injection/copy/status-copy";
import type { StatementPreview } from "@/features/sql-injection/model/types";
import { cn } from "@/lib/utils";

/** Explains, under the preview, what the current statement means. */
export function StatusBox({ preview }: { preview: StatementPreview }) {
  const copy = statusCopy(preview);
  const Icon = copy.tone === "safe" ? ShieldCheck : TriangleAlert;

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-md px-3.5 py-3 md:px-4 md:py-3.5",
        copy.tone === "safe" ? "bg-code-safe-bg" : "bg-code-unsafe-bg",
      )}
    >
      <Icon
        aria-hidden="true"
        className={cn(
          "mt-px hidden size-5 flex-none md:block",
          copy.tone === "safe" ? "text-code-keyword" : "text-code-escaped",
        )}
      />
      <div className="flex flex-col gap-1">
        <p className="text-sm font-semibold text-code-title">
          <span className="md:hidden">{copy.shortTitle}</span>
          <span className="hidden md:inline">{copy.title}</span>
        </p>
        <p className="text-[13px] leading-normal text-code-soft">
          <span className="md:hidden">{copy.shortBody}</span>
          <span className="hidden md:inline">{copy.body}</span>
        </p>
      </div>
    </div>
  );
}
