import { useEffect, useRef, useState } from "react";

import { previewStatement } from "../api";
import type { Db, StatementPreview, StatementRequest } from "../types";

const DEBOUNCE_MS = 150;

type PreviewState = {
  preview: StatementPreview | null;
  error: string | null;
};

/**
 * Live preview of the statement for `request`. Requests are debounced and a
 * response is only applied if no newer request has started since.
 */
export function useStatementPreview(
  db: Db,
  request: StatementRequest,
): PreviewState {
  const [state, setState] = useState<PreviewState>({
    preview: null,
    error: null,
  });
  const isFirstRun = useRef(true);
  const { row, parameterized } = request;
  const { name, email, country, plan } = row;

  useEffect(() => {
    const controller = new AbortController();
    const delay = isFirstRun.current ? 0 : DEBOUNCE_MS;
    isFirstRun.current = false;

    const timer = setTimeout(() => {
      previewStatement(
        db,
        { row: { name, email, country, plan }, parameterized },
        controller.signal,
      )
        .then((preview) => setState({ preview, error: null }))
        .catch((error: unknown) => {
          if (controller.signal.aborted) return;
          setState((current) => ({
            preview: current.preview,
            error: error instanceof Error ? error.message : String(error),
          }));
        });
    }, delay);

    // A newer change (or unmount) cancels the timer and any request in flight,
    // so stale responses are never applied.
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [db, name, email, country, plan, parameterized]);

  return state;
}
