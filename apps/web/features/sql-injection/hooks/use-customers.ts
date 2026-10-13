import { useCallback, useEffect, useState } from "react";

import {
  listCustomers,
  PAGE_SIZE,
} from "@/features/sql-injection/api/endpoints";
import type { Customer, Db } from "@/features/sql-injection/model/types";

type Loaded = {
  /** Which request this data answers; compared to detect loading. */
  key: string;
  rows: Customer[];
  total: number;
  error: string | null;
};

function requestKey(db: Db, page: number, version: number) {
  return `${db}:${page}:${version}`;
}

function pageCountFor(totalRows: number) {
  return Math.max(1, Math.ceil(totalRows / PAGE_SIZE));
}

/**
 * The demo table, one page at a time. `refresh` reloads the current page
 * (after an insert or reset).
 */
export function useCustomers(db: Db) {
  const [page, setPage] = useState(1);
  const [version, setVersion] = useState(0);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const key = requestKey(db, page, version);

  useEffect(() => {
    const requested = requestKey(db, page, version);
    const controller = new AbortController();
    listCustomers(db, page, controller.signal)
      .then((data) =>
        setLoaded({
          key: requested,
          rows: data.rows,
          total: data.total,
          error: null,
        }),
      )
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setLoaded({
          key: requested,
          rows: [],
          total: 0,
          error: error instanceof Error ? error.message : String(error),
        });
      });
    return () => controller.abort();
  }, [db, page, version]);

  const refresh = useCallback(() => setVersion((v) => v + 1), []);
  const total = loaded?.total ?? 0;
  const error = loaded?.error ?? null;
  const loading = loaded?.key !== key;
  const pageCount = pageCountFor(total);

  // The table can shrink under us (another tab, an injected DELETE): stay on a
  // page that exists instead of showing an empty one past the end.
  if (!loading && !error && page > pageCount) {
    setPage(pageCount);
  }

  return {
    rows: loaded?.rows ?? [],
    total,
    error,
    /** True until the first response arrives. */
    initialLoading: loaded === null,
    page,
    pageCount,
    setPage,
    /** Jump to the last page of a table with `totalRows` rows. */
    showLastPage: (totalRows: number) => setPage(pageCountFor(totalRows)),
    refresh,
  };
}
