import { RotateCcw } from "lucide-react";

import { cn } from "@/lib/utils";

type ResetButtonProps = {
  onReset: () => void;
  resetting: boolean;
};

/** "Reset demo data" with its label (wide screens). */
export function ResetButton({ onReset, resetting }: ResetButtonProps) {
  return (
    <button
      type="button"
      onClick={onReset}
      disabled={resetting}
      className="inline-flex h-10 items-center gap-1.5 rounded-md border border-input bg-card px-3 text-[13px] font-medium transition-colors hover:border-input-hover focus-visible:outline-2 focus-visible:outline-offset-2 disabled:opacity-60"
    >
      <ResetIcon spinning={resetting} className="size-4" />
      Reset demo data
    </button>
  );
}

/** Icon-only "Reset demo data" (narrow screens). */
export function ResetIconButton({ onReset, resetting }: ResetButtonProps) {
  return (
    <button
      type="button"
      onClick={onReset}
      disabled={resetting}
      aria-label="Reset demo data"
      className="flex size-11 items-center justify-center rounded-lg border border-input bg-card focus-visible:outline-2 focus-visible:outline-offset-2 disabled:opacity-60 md:hidden"
    >
      <ResetIcon spinning={resetting} className="size-[18px]" />
    </button>
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
