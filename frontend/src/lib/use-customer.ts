"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Me } from "@/lib/types";

export type CustomerState = { status: "loading" } | { status: "guest" } | { status: "signed-in"; me: Me };

/**
 * The signed-in customer, if any. The session cookie is httpOnly, so the browser asks the API (`/auth/me`), which also
 * returns the CSRF token needed for every change.
 */
export function useCustomer() {
  const [state, setState] = useState<CustomerState>({ status: "loading" });

  const refresh = useCallback(async () => {
    try {
      const me = await api<Me>("/auth/me");
      setState({ status: "signed-in", me });
    } catch {
      setState({ status: "guest" });
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    api<Me>("/auth/me")
      .then((me) => !cancelled && setState({ status: "signed-in", me }))
      .catch(() => !cancelled && setState({ status: "guest" }));
    return () => {
      cancelled = true;
    };
  }, []);

  const signedIn = useCallback((me: Me) => setState({ status: "signed-in", me }), []);
  const signedOut = useCallback(() => setState({ status: "guest" }), []);

  return { state, refresh, signedIn, signedOut };
}
