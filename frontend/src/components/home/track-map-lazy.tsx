"use client";

import dynamic from "next/dynamic";
import { TRACK_VIEWBOX } from "@/content/track";

// The map is heavy, never changes and is decorative: draw it in the browser (its script is cached) instead of rendering
// ~150 KB of SVG into every home page. The placeholder keeps the exact shape so nothing jumps when it appears.
const TrackMap = dynamic(() => import("@/components/track-map").then((m) => m.TrackMap), {
  ssr: false,
  loading: () => (
    <div
      aria-hidden="true"
      className="rounded-[2rem] bg-surface-2 ring-1 ring-black/5"
      style={{ aspectRatio: `${TRACK_VIEWBOX.width} / ${TRACK_VIEWBOX.height}` }}
    />
  ),
});

export function TrackMapLazy() {
  return <TrackMap />;
}
