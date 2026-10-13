import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

const TONE_CLASS = {
  neutral: "border-input bg-card text-foreground hover:border-input-hover",
  info: "border-info bg-info-soft text-info-strong hover:border-info-strong",
  warning:
    "border-warning-border bg-warning-soft text-warning-strong hover:border-warning-strong",
} as const;

type QuickFillChipProps = ComponentProps<"button"> & {
  tone?: keyof typeof TONE_CLASS;
};

/** Pill on narrow screens, compact chip on wide ones. */
export function QuickFillChip({
  tone = "neutral",
  className,
  ...props
}: QuickFillChipProps) {
  return (
    <button
      type="button"
      className={cn(
        "inline-flex h-11 flex-none items-center gap-1.5 rounded-full border px-3.5 text-[13px] font-medium whitespace-nowrap transition-colors",
        "focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-input",
        "md:h-9 md:rounded-md md:px-3",
        "[&_svg]:hidden [&_svg]:size-[15px] md:[&_svg]:block",
        TONE_CLASS[tone],
        className,
      )}
      {...props}
    />
  );
}
