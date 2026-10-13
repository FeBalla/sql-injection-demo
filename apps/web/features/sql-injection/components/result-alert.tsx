import {
  CircleAlert,
  CircleCheck,
  RotateCcw,
  TriangleAlert,
  X,
} from "lucide-react";

import { cn } from "@/lib/utils";

export type ResultMessage = {
  tone: "success" | "info" | "warning" | "error";
  title: string;
  body?: string;
  /** Raw database error, shown in mono. */
  detail?: string;
};

const TONE = {
  success: {
    icon: CircleCheck,
    className: "border-info/30 bg-info-soft text-info-strong",
  },
  info: {
    icon: RotateCcw,
    className: "border-info/30 bg-info-soft text-info-strong",
  },
  warning: {
    icon: TriangleAlert,
    className: "border-warning-border bg-warning-soft text-warning-strong",
  },
  error: {
    icon: CircleAlert,
    className: "border-warning-border bg-warning-soft text-warning-strong",
  },
} as const;

export function ResultAlert({
  message,
  onDismiss,
}: {
  message: ResultMessage;
  onDismiss: () => void;
}) {
  const { icon: Icon, className } = TONE[message.tone];
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-2xl border py-3 pr-2 pl-4 md:rounded-xl md:py-3.5",
        className,
      )}
    >
      <Icon aria-hidden="true" className="mt-0.5 size-5 flex-none" />
      <div className="flex min-w-0 flex-1 flex-col gap-1 py-px">
        <p className="text-sm font-semibold">{message.title}</p>
        {message.body && (
          <p className="text-[13px] leading-normal text-foreground">
            {message.body}
          </p>
        )}
        {message.detail && (
          <pre className="font-mono text-xs leading-normal break-words whitespace-pre-wrap">
            {message.detail}
          </pre>
        )}
      </div>
      <button
        type="button"
        aria-label="Dismiss"
        onClick={onDismiss}
        className="-my-1.5 flex size-11 flex-none items-center justify-center rounded-md transition-colors hover:bg-black/5 focus-visible:outline-2 md:size-9"
      >
        <X aria-hidden="true" className="size-4" />
      </button>
    </div>
  );
}
