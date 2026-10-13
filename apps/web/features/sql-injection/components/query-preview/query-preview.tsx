import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { CodeLines } from "@/features/sql-injection/components/shared/code-lines";
import type { StatementPreview } from "@/features/sql-injection/model/types";
import { useScrollFade } from "@/hooks/use-scroll-fade";
import { cn } from "@/lib/utils";

import { BoundParamsList } from "./bound-params-list";
import { StatusBox } from "./status-box";

type QueryPreviewProps = {
  preview: StatementPreview | null;
  error: string | null;
  parameterized: boolean;
  onParameterizedChange: (value: boolean) => void;
  className?: string;
};

/** Dark panel with the live statement, its bound parameters and an explanation. */
export function QueryPreview({
  preview,
  error,
  parameterized,
  onParameterizedChange,
  className,
}: QueryPreviewProps) {
  const codeRef = useScrollFade<HTMLDivElement>();
  return (
    <section
      aria-labelledby="preview-title"
      className={cn(
        "flex flex-col overflow-hidden rounded-2xl bg-code text-code-foreground md:rounded-xl",
        className,
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-code-border px-4 py-3.5 md:px-5 md:py-4">
        <div className="flex flex-col gap-0.5">
          <h2
            id="preview-title"
            className="text-[15px] font-semibold text-code-title"
          >
            Query preview
          </h2>
          <span className="hidden text-xs text-code-muted md:block">
            Updates live as you type
          </span>
        </div>
        <div className="flex items-center gap-2.5">
          <Label
            htmlFor="parameterized"
            className="text-[13px] font-normal text-code-soft"
          >
            Parameterized
          </Label>
          <Switch
            id="parameterized"
            size="lg"
            checked={parameterized}
            onCheckedChange={onParameterizedChange}
            className="focus-visible:ring-code-keyword/60 data-checked:bg-info data-unchecked:bg-code-switch-off"
          />
        </div>
      </div>

      <div
        ref={codeRef}
        aria-live="off"
        aria-label="SQL statement"
        role="region"
        className="overflow-x-auto py-3 data-more:[mask-image:linear-gradient(to_right,#000_calc(100%-2rem),transparent)] md:py-4"
      >
        {preview ? (
          <CodeLines lines={preview.lines} />
        ) : (
          !error && (
            <p className="px-5 font-mono text-[13px] text-code-muted">
              Building the statement…
            </p>
          )
        )}
        {error && (
          <p role="alert" className="px-5 pt-2 text-[13px] text-code-escaped">
            Preview unavailable: {error}
          </p>
        )}
      </div>

      {preview && preview.params.length > 0 && (
        <BoundParamsList preview={preview} />
      )}

      {preview && (
        <div className="mx-4 mt-auto mb-4 md:mx-5 md:mb-5">
          <StatusBox preview={preview} />
        </div>
      )}
    </section>
  );
}
