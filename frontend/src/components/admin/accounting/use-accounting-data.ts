"use client";

import { useCallback, useEffect, useState } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import type { Account } from "@/lib/accounting";

/** The accounts (the till, the bank and the income and expense categories) every accounting screen needs. */
export function useAccountingData() {
  const { call } = useAdmin();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      setAccounts(await call<Account[]>("/accounting/accounts"));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطا");
    } finally {
      setReady(true);
    }
  }, [call]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- the first fetch of this screen
    void reload();
  }, [reload]);

  return { accounts, ready, error, reload };
}
