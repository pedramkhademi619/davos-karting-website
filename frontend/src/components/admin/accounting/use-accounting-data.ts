"use client";

import { useCallback, useEffect, useState } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import type { Account, Vendor } from "@/lib/accounting";

/** The chart of accounts and the suppliers, which almost every accounting screen needs for its drop-downs. */
export function useAccountingData() {
  const { call } = useAdmin();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const [a, v] = await Promise.all([call<Account[]>("/accounting/accounts"), call<Vendor[]>("/accounting/vendors")]);
      setAccounts(a);
      setVendors(v);
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

  return { accounts, vendors, ready, error, reload };
}
