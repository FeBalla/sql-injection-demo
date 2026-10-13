import { useCallback, useEffect, useState } from "react";

import { listDatabases } from "@/features/sql-injection/api/endpoints";
import type { DatabaseInfo } from "@/features/sql-injection/model/types";

/** Shown until GET /databases answers, so the pickers render immediately. */
const FALLBACK: DatabaseInfo[] = [
  {
    id: "postgres",
    label: "Postgres",
    table: "public.customers",
    available: true,
    reason: null,
  },
  {
    id: "bigquery",
    label: "BigQuery",
    table: "",
    available: false,
    reason: "Checking availability…",
  },
];

export function useDatabases() {
  const [databases, setDatabases] = useState<DatabaseInfo[]>(FALLBACK);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let active = true;
    listDatabases()
      .then((list) => {
        if (active) setDatabases(list);
      })
      .catch(() => {
        // Keep the last known list; the table shows the connection error.
      });
    return () => {
      active = false;
    };
  }, [version]);

  const refresh = useCallback(() => setVersion((v) => v + 1), []);
  return { databases, refresh };
}
