"use client";

import { useEffect } from "react";

/** Remembers for the rest of the browser session that the intro has played (read by the site layout). */
export function IntroSeen() {
  useEffect(() => {
    document.cookie = "davos_intro=1; path=/; SameSite=Lax";
  }, []);
  return null;
}
