"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { KartShape } from "@/components/kart-shape";
import { SMOOTHING, START_INDEX, TRACK_POINTS, TRACK_VIEWBOX, TRACK_WIDTHS } from "@/content/track";
import { fa } from "@/lib/format";
import { circuitPath, nearestIndex, smoothTrack } from "@/lib/track-geometry";

export type Sector = { key: string; label: string; ms: number | null };

/** The real Davos circuit, starting at the start/finish line, as one SVG path. */
function useCircuit() {
  return useMemo(() => {
    const track = smoothTrack(TRACK_POINTS, TRACK_WIDTHS, SMOOTHING);
    const start = nearestIndex(track.points, TRACK_POINTS[START_INDEX]);
    const rotated = [...track.points.slice(start), ...track.points.slice(0, start)];
    return { d: circuitPath(rotated), start: rotated[0] };
  }, []);
}

/** Sector time colour, F1 style: purple for a flier, green for a good one, yellow otherwise. */
export function sectorTone(ms: number): string {
  if (ms < 9000) return "#b46bff";
  if (ms < 25000) return "#1ee07a";
  return "#ffc400";
}

export function seconds(ms: number): string {
  return fa((ms / 1000).toFixed(1)).replace(".", "٫");
}

/**
 * The wizard's progress bar: a kart driving round the real Davos circuit (one corner per step), with an F1-style timing
 * row underneath that shows how long each step took.
 */
export function LapTracker({ progress, sectors, compact = false }: { progress: number; sectors: Sector[]; compact?: boolean }) {
  const circuit = useCircuit();
  // Measured on a plain copy of the path: the drawn one has pathLength=1, which would rescale getPointAtLength.
  const pathRef = useRef<SVGPathElement>(null);
  const [kart, setKart] = useState<{ x: number; y: number; p: number; angle: number } | null>(null);
  const shown = useRef(progress);

  // Drive the kart from where it is to the new progress along the path (eased, ~1 s; instant with reduced motion).
  useEffect(() => {
    const path = pathRef.current;
    if (!path) return;
    const length = path.getTotalLength();
    const from = shown.current;
    const to = progress;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const place = (p: number) => {
      const at = Math.min(0.9999, Math.max(0, p)) * length;
      const point = path.getPointAtLength(at);
      const ahead = path.getPointAtLength(Math.min(length, at + 2)); // the kart faces where the track goes next
      const angle = (Math.atan2(ahead.y - point.y, ahead.x - point.x) * 180) / Math.PI;
      setKart({ x: point.x, y: point.y, p, angle });
    };
    if (reduce || from === to) {
      shown.current = to;
      place(to);
      return;
    }
    let frame = 0;
    const started = performance.now();
    const duration = 1100;
    const tick = (now: number) => {
      const t = Math.min(1, (now - started) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      const p = from + (to - from) * eased;
      shown.current = p;
      place(p);
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [progress]);

  const vb = `${TRACK_VIEWBOX.x} ${TRACK_VIEWBOX.y} ${TRACK_VIEWBOX.width} ${TRACK_VIEWBOX.height}`;
  return (
    <div className={compact ? "flex items-center gap-3" : ""}>
      <div className={compact ? "w-[6.5rem] shrink-0 sm:w-32" : "relative"}>
        <svg viewBox={vb} className="h-auto w-full" role="img" aria-label={`پیشرفت رزرو: ${fa(Math.round(progress * 100))} درصد`}>
          <defs>
            <filter id="lap-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="6" result="b" />
              <feMerge>
                <feMergeNode in="b" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <path d={circuit.d} fill="none" stroke="rgb(255 255 255 / 0.07)" strokeWidth="30" strokeLinejoin="round" />
          <path d={circuit.d} fill="none" stroke="rgb(255 255 255 / 0.18)" strokeWidth="2" strokeDasharray="6 10" />
          <path ref={pathRef} d={circuit.d} fill="none" stroke="none" />
          <path
            d={circuit.d}
            fill="none"
            stroke="#ffc400"
            strokeWidth="7"
            strokeLinecap="round"
            pathLength={1}
            strokeDasharray={1}
            strokeDashoffset={1 - (kart ? kart.p : progress)}
            filter="url(#lap-glow)"
          />
          <g transform={`translate(${circuit.start[0]} ${circuit.start[1]})`}>
            <rect x="-17" y="-5" width="34" height="10" rx="2" fill="#fff" />
            <rect x="-17" y="-5" width="8.5" height="5" fill="#111" />
            <rect x="0" y="-5" width="8.5" height="5" fill="#111" />
            <rect x="-8.5" y="0" width="8.5" height="5" fill="#111" />
            <rect x="8.5" y="0" width="8.5" height="5" fill="#111" />
          </g>
          {kart && (
            <g transform={`translate(${kart.x} ${kart.y})`}>
              <circle r="22" fill="rgb(255 196 0 / 0.25)" />
              <g transform={`rotate(${kart.angle}) scale(1.25)`}>
                <KartShape colour="#ffc400" />
              </g>
            </g>
          )}
        </svg>
      </div>
      <ol className={`grid grid-cols-4 gap-1.5 ${compact ? "flex-1" : "mt-4"}`} aria-label="زمان هر مرحله">
        {sectors.map((sector, index) => {
          const done = sector.ms !== null;
          const tone = done ? sectorTone(sector.ms!) : undefined;
          return (
            <li key={sector.key} className="min-w-0">
              <span
                className="block h-1.5 rounded-full transition-colors duration-500"
                style={{ background: tone ?? "rgb(255 255 255 / 0.1)", boxShadow: tone ? `0 0 12px ${tone}` : undefined }}
              />
              <span className="mt-1.5 flex items-baseline justify-between gap-1 text-[0.68rem] leading-tight sm:text-xs">
                <span className="race-number font-bold text-on-carbon-muted" dir="ltr">
                  {index < 3 ? `S${index + 1}` : "FIN"}
                </span>
                <span className="truncate font-bold" style={{ color: tone ?? "rgb(255 255 255 / 0.35)" }}>
                  {done ? seconds(sector.ms!) : sector.label}
                </span>
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
