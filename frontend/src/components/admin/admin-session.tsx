"use client";

import { createContext, useContext } from "react";
import { ApiError, api, type RequestOptions } from "@/lib/api";
import type { AdminMe } from "@/lib/types";

export type AdminSession = {
  me: AdminMe;
  isOwner: boolean;
  /** Calls the admin API; changes carry the staff CSRF token, and an expired session signs the panel out. */
  call: <T>(path: string, options?: Omit<RequestOptions, "csrf">) => Promise<T>;
  signOut: () => void;
};

export const AdminSessionContext = createContext<AdminSession | null>(null);

export function useAdmin(): AdminSession {
  const session = useContext(AdminSessionContext);
  if (!session) throw new Error("useAdmin must be used inside the admin panel");
  return session;
}

export function makeSession(me: AdminMe, signOut: () => void): AdminSession {
  return {
    me,
    isOwner: me.role === "owner",
    signOut,
    call: async <T,>(path: string, options: Omit<RequestOptions, "csrf"> = {}) => {
      const method = options.method ?? "GET";
      try {
        return await api<T>(`/admin${path}`, { ...options, csrf: method === "GET" ? undefined : me.csrf_token });
      } catch (error) {
        if (error instanceof ApiError && error.isUnauthenticated) signOut();
        throw error;
      }
    },
  };
}
