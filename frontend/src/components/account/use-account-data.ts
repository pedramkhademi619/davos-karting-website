"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, api, errorMessage } from "@/lib/api";
import type { AccountPayment, Profile, Reservation } from "@/lib/types";

export type AccountData = {
  profile: Profile;
  reservations: Reservation[];
  payments: AccountPayment[];
};

const fetchAll = () =>
  Promise.all([
    api<Profile>("/account/profile"),
    api<Reservation[]>("/account/reservations"),
    api<AccountPayment[]>("/account/payments"),
  ]).then(([profile, reservations, payments]): AccountData => ({ profile, reservations, payments }));

/** Everything the account page shows, loaded together; `reload` refreshes it in place (no spinner). */
export function useAccountData(onSignedOut: () => void) {
  const [data, setData] = useState<AccountData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fail = useCallback(
    (err: unknown) => {
      if (err instanceof ApiError && err.isUnauthenticated) onSignedOut();
      else setError(errorMessage(err));
    },
    [onSignedOut],
  );

  const reload = useCallback(() => fetchAll().then(setData).catch(fail), [fail]);

  useEffect(() => {
    let cancelled = false;
    fetchAll()
      .then((value) => !cancelled && setData(value))
      .catch((err) => !cancelled && fail(err));
    return () => {
      cancelled = true;
    };
  }, [fail]);

  const setProfile = useCallback((profile: Profile) => setData((current) => (current ? { ...current, profile } : current)), []);

  return { data, error, reload, setProfile };
}

export const isOpenTicket = (t: Reservation) => t.status === "held" || t.status === "confirmed";

/** Numbers for the overview, derived from the lists so they can never disagree with them. */
export function accountStats(reservations: Reservation[], payments: AccountPayment[]) {
  const upcoming = reservations.filter(isOpenTicket);
  const attended = reservations.filter((t) => t.status === "attended");
  const paid = payments.filter((p) => p.status === "paid");
  return {
    upcoming: upcoming.length,
    visits: attended.length,
    karts: attended.reduce((sum, t) => sum + t.single_count + t.double_count, 0),
    paidToman: paid.reduce((sum, p) => sum + p.amount_toman, 0),
    paidCount: paid.length,
  };
}
