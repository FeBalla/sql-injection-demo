import { useRef, useState } from "react";

import type { ResultMessage } from "@/features/sql-injection/copy/result-messages";

/**
 * The alert above the table. Attach `alertRef` to its container so
 * `showMessage` can scroll it into view: on narrow screens it can be
 * off-screen.
 */
export function useResultMessage() {
  const [message, setMessage] = useState<ResultMessage | null>(null);
  const alertRef = useRef<HTMLDivElement>(null);

  function showMessage(next: ResultMessage) {
    setMessage(next);
    requestAnimationFrame(() =>
      alertRef.current?.scrollIntoView({
        block: "nearest",
        behavior: "smooth",
      }),
    );
  }

  function dismissMessage() {
    setMessage(null);
  }

  return { message, alertRef, showMessage, dismissMessage };
}
