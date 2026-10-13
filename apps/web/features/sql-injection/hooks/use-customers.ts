import { useCallback, useEffect, useState } from "react";

import { listCustomers, PAGE_SIZE } from "../api";
import type { Customer, Db } from "../types";

type Loaded = {
  /** Which request this data answers; compared to detect loading. */
  key: string;
  rows: Customer[];
  total: number;
  error: string | null;
};

/** One page of the demo table. `refresh` reloads it (after an insert or reset). */
export function useCustomers(db: Db, page: number) {
  const [version, setVersion] = useState(0);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const key = `${db}:${page}:${version}`;

  useEffect(() => {
    const controller = new AbortController();
    listCustomers(db, page, controller.signal)
      .then((data) =>
        setLoaded({ key, rows: data.rows, total: data.total, error: null }),
      )
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setLoaded({
          key,
          rows: [],
          total: 0,
          error: error instanceof Error ? error.message : String(error),
        });
      });
    return () => controller.abort();
  }, [db, page, key]);

  const refresh = useCallback(() => setVersion((v) => v + 1), []);
  const total = loaded?.total ?? 0;

  return {
    rows: loaded?.rows ?? [],
    total,
    error: loaded?.error ?? null,
    loading: loaded?.key !== key,
    /** True until the first response arrives. */
    initialLoading: loaded === null,
    pageCount: Math.max(1, Math.ceil(total / PAGE_SIZE)),
    refresh,
  };
}
