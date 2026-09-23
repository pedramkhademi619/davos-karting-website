import {
  APRON,
  APRON_TOP_EDGE,
  BUILDING,
  FENCES,
  GRANDSTAND,
  LEFT_ROAD,
  LEFT_ROAD_EDGE,
  PIT_BOXES,
  PLANTER,
  SMOOTHING,
  START_INDEX,
  STEPS,
  TERRACE,
  TRACK_POINTS,
  TRACK_VIEWBOX,
  TRACK_WIDTHS,
  TYRE_COLOURS,
  VEGETATION,
} from "@/content/track";
import { buildRibbon, circuitPath, edgePath, headingAt, insidePolygon, loopPath, nearestIndex, polygonPath, smoothTrack } from "@/lib/track-geometry";

// Illustration colours, deliberately independent of the site's UI tokens.
const INK = "#111114";
const ASPHALT = "#34343A";
const SOIL = "#E6CDB0";
const TYRE_SIZE = 8.2;
const TYRE_PITCH = 10.4; // centre to centre; colours alternate, so each colour repeats every two tyres
const TYRE_GAP = 5.6; // asphalt edge to tyre centre

// The traced waypoints are a pixel or two off the true line; smoothing them gives clean straights and even bends (deviation from the trace stays under about 2 units).
const TRACK = smoothTrack(TRACK_POINTS, TRACK_WIDTHS, SMOOTHING);
const RIBBON = buildRibbon(TRACK.points, TRACK.widths);
const CIRCUIT = circuitPath(TRACK.points);
const ROAD = loopPath(RIBBON.left) + loopPath(RIBBON.right);
const APRON_PATH = polygonPath(APRON);
// Tyres line the whole track on both sides, except across the open paved apron.
const onApron = (x: number, y: number) => insidePolygon(x, y, APRON);
const TYRES = edgePath(RIBBON, 1, TYRE_GAP, onApron) + edgePath(RIBBON, -1, TYRE_GAP, onApron);
const START_INDEX_SMOOTH = nearestIndex(TRACK.points, TRACK_POINTS[START_INDEX]);
const START = TRACK.points[START_INDEX_SMOOTH];
const START_HEADING = headingAt(TRACK.points, START_INDEX_SMOOTH);
const START_WIDTH = TRACK.widths[START_INDEX_SMOOTH];

function Kart({ body, duration, begin }: { body: string; duration: number; begin: number }) {
  return (
    <g className="kart">
      <rect x="-8.5" y="-4.6" width="17" height="9.2" rx="3.2" fill={body} stroke={INK} strokeWidth="1.5" />
      <circle cx="-1" cy="0" r="2.4" fill={INK} />
      <animateMotion dur={`${duration}s`} begin={`${begin}s`} repeatCount="indefinite" rotate="auto">
        <mpath href="#circuit-path" />
      </animateMotion>
    </g>
  );
}

/**
 * Top-down map of the track, drawn from the traced data in content/track.ts. Decorative artwork with a text alternative; the karts
 * are hidden when the visitor prefers reduced motion.
 */
export function TrackMap({ className }: { className?: string }) {
  const { x, y, width, height } = TRACK_VIEWBOX;
  const period = TYRE_PITCH * 2 - 0.01;

  return (
    <figure className={className}>
      <div className="overflow-hidden rounded-[2rem] bg-surface-2 shadow-[0_1px_0_rgb(17_17_20/0.04),0_44px_80px_-36px_rgb(90_65_10/0.45)] ring-1 ring-black/5">
        <svg viewBox={`${x} ${y} ${width} ${height}`} role="img" aria-labelledby="track-map-title" className="block h-auto w-full">
          <title id="track-map-title">نقشه پیست کارتینگ داوس از نمای بالا</title>
          <defs>
            <linearGradient id="soil" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#EED9C2" />
              <stop offset="1" stopColor="#E4CAAC" />
            </linearGradient>
            <pattern id="speckle" width="46" height="46" patternUnits="userSpaceOnUse">
              <circle cx="6" cy="9" r="1.3" fill="#9A7654" />
              <circle cx="21" cy="31" r="1" fill="#9A7654" />
              <circle cx="37" cy="14" r="1.5" fill="#8A6A4C" />
              <circle cx="30" cy="42" r="1.1" fill="#9A7654" />
              <circle cx="12" cy="24" r="0.9" fill="#8A6A4C" />
            </pattern>
            <pattern id="terrace" width="22" height="22" patternUnits="userSpaceOnUse">
              <rect width="22" height="22" fill="#FFC400" />
              <rect width="11" height="11" fill={INK} />
              <rect x="11" y="11" width="11" height="11" fill={INK} />
            </pattern>
            <pattern id="flag" width="7" height="7" patternUnits="userSpaceOnUse">
              <rect width="7" height="7" fill="#fff" />
              <rect width="3.5" height="3.5" fill={INK} />
              <rect x="3.5" y="3.5" width="3.5" height="3.5" fill={INK} />
            </pattern>
            <pattern id="stands" width="6" height="6" patternUnits="userSpaceOnUse">
              <rect width="6" height="6" fill="#D8D0C4" />
              <rect width="6" height="2" fill="#BFB5A6" />
            </pattern>
            <pattern id="steps" width="23" height="13" patternUnits="userSpaceOnUse">
              <rect width="23" height="13" fill="#DDD6CA" />
              <rect x="1" y="1.5" width="21" height="10" rx="1.5" fill="#FFFFFF" />
            </pattern>
            <filter id="soft" x="-10%" y="-10%" width="120%" height="120%">
              <feGaussianBlur stdDeviation="2.4" />
            </filter>
            <path id="circuit-path" d={CIRCUIT} />
            <path id="tyre-path" d={TYRES} />
          </defs>

          {/* Ground. */}
          <rect x={x} y={y} width={width} height={height} fill="url(#soil)" />
          <rect x={x} y={y} width={width} height={height} fill="url(#speckle)" opacity="0.5" />

          {/* Scrub and grass patches. */}
          <g filter="url(#soft)" fill="#7F9A6B" fillOpacity="0.62">
            {VEGETATION.map((d) => (
              <path key={d.slice(0, 24)} d={d} />
            ))}
          </g>

          {/* The street on the left, the building at the top-left corner and the grandstand. */}
          <path d={LEFT_ROAD} fill="#D9D3C9" />
          <path d={LEFT_ROAD_EDGE} stroke="#5A4A3E" strokeWidth="3" strokeLinecap="round" fill="none" />
          <ellipse cx={BUILDING.cx} cy={BUILDING.cy} rx={BUILDING.rx} ry={BUILDING.ry} fill="#ECE8E0" stroke="#4A382C" strokeWidth="3.5" />
          <ellipse cx={BUILDING.cx + 4} cy={BUILDING.cy - 2} rx={BUILDING.rx * 0.68} ry={BUILDING.ry * 0.66} fill="none" stroke="#CFC8BC" strokeWidth="2" />
          <path d={GRANDSTAND} fill="url(#stands)" stroke="#A89E90" strokeWidth="1.2" />
          <rect x={TERRACE.x} y={TERRACE.y} width={TERRACE.width} height={TERRACE.height} fill="url(#terrace)" stroke={INK} strokeWidth="1" />

          {/* The road: asphalt between the two traced edges, with the white edge lines. */}
          <path d={ROAD} fill={ASPHALT} fillRule="evenodd" stroke="#FFFFFF" strokeWidth="1.7" strokeLinejoin="round" strokeOpacity="0.95" />

          {/* The wide paved plaza beside the stands (down to the entrance); the polygon also hides edge lines that are not real there. */}
          <path d={APRON_PATH} fill={ASPHALT} />
          <path d={APRON_TOP_EDGE} fill="none" stroke="#FFFFFF" strokeWidth="1.7" strokeLinejoin="round" opacity="0.95" />
          <rect x={PLANTER.x} y={PLANTER.y} width={PLANTER.width} height={PLANTER.height} rx={PLANTER.radius} fill={SOIL} stroke="#FFFFFF" strokeWidth="2" />
          <rect x={STEPS.x} y={STEPS.y} width={STEPS.width} height={STEPS.height} fill="url(#steps)" />
          {PIT_BOXES.map(([bx, by]) => (
            <rect key={bx} x={bx} y={by} width="12" height="26" rx="1.5" fill="#FFFFFF" stroke="#CFC8BC" strokeWidth="1" />
          ))}

          {/* Yellow and red tyres lining the whole track: a soft shadow, the two colours alternating, then the dark hole of each tyre. */}
          <g fill="none" strokeLinecap="round">
            <use href="#tyre-path" stroke={INK} strokeOpacity="0.28" strokeWidth={TYRE_SIZE + 1.8} strokeDasharray={`0.01 ${TYRE_PITCH - 0.01}`} />
            <use href="#tyre-path" stroke={TYRE_COLOURS[0]} strokeWidth={TYRE_SIZE} strokeDasharray={`0.01 ${period}`} />
            <use href="#tyre-path" stroke={TYRE_COLOURS[1]} strokeWidth={TYRE_SIZE} strokeDasharray={`0.01 ${period}`} strokeDashoffset={-TYRE_PITCH} />
            <use href="#tyre-path" stroke="#2A2018" strokeOpacity="0.85" strokeWidth="3" strokeDasharray={`0.01 ${TYRE_PITCH - 0.01}`} />
          </g>

          {/* Start/finish line across the lane beside the stands. */}
          <g transform={`translate(${START[0]} ${START[1]}) rotate(${START_HEADING})`}>
            <rect x="-3.5" y={-START_WIDTH / 2} width="7" height={START_WIDTH} fill="url(#flag)" />
          </g>

          <Kart body={TYRE_COLOURS[0]} duration={26} begin={0} />
          <Kart body={TYRE_COLOURS[1]} duration={29} begin={-12} />

          {/* Boundary fences. */}
          {FENCES.map((fence) => (
            <path key={fence.d} d={fence.d} fill="none" stroke="#3D322A" strokeWidth={fence.width} strokeDasharray={fence.dash} strokeLinecap="round" opacity={fence.opacity} />
          ))}
        </svg>
      </div>
      <figcaption className="mt-3 text-sm text-fg-subtle">نقشه پیست بر پایه تصویر هوایی؛ جزئیات اطراف پیست تقریبی است.</figcaption>
    </figure>
  );
}
