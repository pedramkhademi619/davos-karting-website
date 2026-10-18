import { KartShape } from "@/components/kart-shape";
import { SMOOTHING, START_INDEX, TRACK_POINTS, TRACK_VIEWBOX, TRACK_WIDTHS } from "@/content/track";
import { circuitPath, headingAt, nearestIndex, smoothTrack } from "@/lib/track-geometry";

// Computed once per server process: the real Davos circuit as a single path, plus the start/finish line.
const TRACK = smoothTrack(TRACK_POINTS, TRACK_WIDTHS, SMOOTHING);
const PATH = circuitPath(TRACK.points);
const START = nearestIndex(TRACK.points, TRACK_POINTS[START_INDEX]);
const [SX, SY] = TRACK.points[START];
const START_ANGLE = headingAt(TRACK.points, START); // degrees
const VIEWBOX = `${TRACK_VIEWBOX.x} ${TRACK_VIEWBOX.y} ${TRACK_VIEWBOX.width} ${TRACK_VIEWBOX.height}`;

/** One kart: a go-kart seen from above with a short comet tail, lapping the circuit nose first (SMIL, no script). */
function Kart({ colour, duration, begin }: { colour: string; duration: number; begin: number }) {
  const lap = (offset: number) => (
    <animateMotion dur={`${duration}s`} begin={`${begin - offset}s`} repeatCount="indefinite" rotate="auto">
      <mpath href="#neon-circuit" />
    </animateMotion>
  );
  return (
    <g className="kart">
      {[0.24, 0.16, 0.08].map((lag, i) => (
        <circle key={lag} r={9 - i * 2.4} fill={colour} opacity={0.18 + i * 0.12}>
          {lap(lag)}
        </circle>
      ))}
      <circle r="22" fill={colour} opacity="0.3" filter="url(#neon-blur)">
        {lap(0)}
      </circle>
      <g>
        {lap(0)}
        {/* The circuit is drawn about 600 units wide, so a kart needs ~2x to read as a kart and not a dot. */}
        <g transform="scale(2.1)">
          <KartShape colour={colour} />
        </g>
      </g>
    </g>
  );
}

/**
 * The real Davos circuit drawn in light: dark asphalt, a neon racing line that draws itself in, the start/finish line,
 * and two karts lapping. Decorative (the full map with every tyre is in the track section).
 */
export function NeonTrack({ className = "" }: { className?: string }) {
  return (
    <svg viewBox={VIEWBOX} className={className} aria-hidden="true" focusable="false">
      <defs>
        <filter id="neon-blur" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="8" />
        </filter>
        <linearGradient id="neon-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#ffd84d" />
          <stop offset="0.55" stopColor="#ffb300" />
          <stop offset="1" stopColor="#ff5a1f" />
        </linearGradient>
      </defs>
      <path id="neon-circuit" d={PATH} fill="none" />
      {/* Asphalt and kerb glow. */}
      <path d={PATH} fill="none" stroke="rgb(255 255 255 / 0.05)" strokeWidth="38" strokeLinejoin="round" />
      <path d={PATH} fill="none" stroke="rgb(0 0 0 / 0.55)" strokeWidth="30" strokeLinejoin="round" />
      <path d={PATH} fill="none" stroke="rgb(255 255 255 / 0.14)" strokeWidth="1.5" strokeDasharray="7 11" />
      {/* The racing line, drawn in once, then glowing. */}
      <path d={PATH} fill="none" stroke="url(#neon-grad)" strokeWidth="10" opacity="0.45" filter="url(#neon-blur)" />
      <path className="neon-draw" d={PATH} pathLength={1} fill="none" stroke="url(#neon-grad)" strokeWidth="3.5" strokeLinecap="round" />
      {/* Start/finish line: a chequered strip across the track. */}
      <g transform={`translate(${SX} ${SY}) rotate(${START_ANGLE + 90})`}>
        {Array.from({ length: 8 }, (_, i) => (
          <g key={i}>
            <rect x={-16 + i * 4} y={-4} width={4} height={4} fill={i % 2 ? "#fff" : "#111"} />
            <rect x={-16 + i * 4} y={0} width={4} height={4} fill={i % 2 ? "#111" : "#fff"} />
          </g>
        ))}
      </g>
      <Kart colour="#ffc400" duration={11} begin={0} />
      <Kart colour="#ff3b2f" duration={11.6} begin={-3.2} />
    </svg>
  );
}
