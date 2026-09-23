import type { CSSProperties } from "react";

/** Delay step for the `rise` entrance animation defined in globals.css (step 0 starts immediately). */
export function stagger(step: number): CSSProperties {
  return { "--i": step } as CSSProperties;
}
