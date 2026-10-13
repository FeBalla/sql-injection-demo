import { useState } from "react";

import { resetCustomers } from "@/features/sql-injection/api/endpoints";
import {
  resetDoneMessage,
  resetFailedMessage,
  type ResultMessage,
} from "@/features/sql-injection/copy/result-messages";
import type { Db } from "@/features/sql-injection/model/types";

type ResetDemoOptions = {
  db: Db;
  /** Table reference used in the message. */
  table: string;
  showMessage: (message: ResultMessage) => void;
  /** After the table is back to its seed rows. */
  onReset: () => void;
  /** After every reset attempt, to reload what it may have changed. */
  onSettled: () => void;
};

/** "Reset demo data": restores the seed rows of the selected database. */
export function useResetDemo({
  db,
  table,
  showMessage,
  onReset,
  onSettled,
}: ResetDemoOptions) {
  const [resetting, setResetting] = useState(false);

  async function reset() {
    setResetting(true);
    try {
      const { total } = await resetCustomers(db);
      onReset();
      showMessage(resetDoneMessage(total, table));
    } catch (error) {
      showMessage(resetFailedMessage(error));
    } finally {
      setResetting(false);
      onSettled();
    }
  }

  return { reset, resetting };
}
