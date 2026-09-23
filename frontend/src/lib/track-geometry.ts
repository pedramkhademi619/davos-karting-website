/** A point in map units. */
export type Point = readonly [x: number, y: number];

const round = (value: number) => Number(value.toFixed(1));

/** Waypoints wrap around, so any integer index is valid. */
function at<T>(items: readonly T[], index: number): T {
  const count = items.length;
  return items[((index % count) + count) % count];
}

/** Uniform Catmull-Rom spline (closed): position and derivative between waypoint `index` and the next one, at t in [0, 1). */
function spline(points: readonly Point[], index: number, t: number) {
  const p0 = at(points, index - 1);
  const p1 = at(points, index);
  const p2 = at(points, index + 1);
  const p3 = at(points, index + 2);
  const t2 = t * t;
  const t3 = t2 * t;
  const coord = (k: 0 | 1) =>
    0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3);
  const slope = (k: 0 | 1) =>
    0.5 * (-p0[k] + p2[k] + 2 * (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t + 3 * (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t2);
  return { x: coord(0), y: coord(1), dx: slope(0), dy: slope(1) };
}

/** Samples are this far apart (map units) along the resampled centre line. */
const SAMPLE_STEP = 2;

/** Gaussian low-pass filter of a closed, evenly sampled series; `spread` is in map units along the line. */
function blurLoop(values: readonly number[], spread: number): number[] {
  const reach = Math.ceil((spread * 3) / SAMPLE_STEP);
  const kernel = Array.from({ length: reach * 2 + 1 }, (_, k) => Math.exp(-(((k - reach) * SAMPLE_STEP) ** 2) / (2 * spread * spread)));
  const total = kernel.reduce((sum, weight) => sum + weight, 0);
  return values.map((_, index) => kernel.reduce((sum, weight, k) => sum + weight * at(values, index + k - reach), 0) / total);
}

/** A closed track, evenly spaced along its length. */
export type SmoothTrack = { points: Point[]; widths: number[] };

/** How strongly `smoothTrack` filters, in map units along the line. */
export type Smoothing = {
  /** Filter width in bends: small, so a bend keeps its radius (a wide filter would pull it tighter). */
  bendSigma: number;
  /** How far (map units) a stretch may stray from a ruler-straight line and still be drawn as one; anything more is split in two. */
  straightTolerance: number;
  /** Turning radius below which a stretch counts as a bend. */
  bendRadius: number;
  /** Filter width for the lane width, which changes only gently. */
  widthSigma: number;
  /** Distance between the waypoints of the result. */
  spacing: number;
};

/**
 * Smooths a hand-traced closed centre line. Tracing by eye leaves waypoints a pixel or two off the true line, and that shows as
 * wobble on the straights and lumpy bends. The line is resampled at even spacing and low-pass filtered (Gaussian) so bends are
 * even; stretches that are nearly straight are then replaced by a ruler-straight line, blending between the two by local curvature. The result is thinned to a waypoint every
 * `spacing` units.
 */
export function smoothTrack(points: readonly Point[], widths: readonly number[], smoothing: Smoothing): SmoothTrack {
  const { bendSigma, straightTolerance, bendRadius, widthSigma, spacing } = smoothing;
  if (points.length !== widths.length) throw new Error("track: every waypoint needs a width");
  const step = SAMPLE_STEP;

  // Dense, evenly spaced samples of the traced spline with the width interpolated.
  const dense: Point[] = [];
  const denseWidths: number[] = [];
  for (let index = 0; index < points.length; index += 1) {
    for (let k = 0; k < 8; k += 1) {
      const { x, y } = spline(points, index, k / 8);
      dense.push([x, y]);
      denseWidths.push(at(widths, index) + (at(widths, index + 1) - at(widths, index)) * (k / 8));
    }
  }
  const cumulative = [0];
  for (let index = 0; index < dense.length; index += 1) {
    const a = dense[index];
    const b = at(dense, index + 1);
    cumulative.push(cumulative[index] + Math.hypot(b[0] - a[0], b[1] - a[1]));
  }
  const length = cumulative[dense.length];
  const count = Math.round(length / step);
  const samples: Point[] = [];
  const sampleWidths: number[] = [];
  for (let index = 0, cursor = 0; index < count; index += 1) {
    const distance = (index * length) / count;
    while (cumulative[cursor + 1] < distance) cursor += 1;
    const f = (distance - cumulative[cursor]) / (cumulative[cursor + 1] - cumulative[cursor]);
    const a = dense[cursor];
    const b = at(dense, cursor + 1);
    samples.push([a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f]);
    sampleWidths.push(denseWidths[cursor] + (at(denseWidths, cursor + 1) - denseWidths[cursor]) * f);
  }

  const bendX = blurLoop(samples.map((p) => p[0]), bendSigma);
  const bendY = blurLoop(samples.map((p) => p[1]), bendSigma);
  // Bendiness 0..1 from the heading change over about 60 units of a coarser copy of the line, so that the leftover wobble of a
  // straight does not read as a bend; it is blurred again so the switch between bend and straight is gradual.
  const coarseX = blurLoop(bendX, 25);
  const coarseY = blurLoop(bendY, 25);
  const lookAhead = 15;
  const bendiness = blurLoop(
    coarseX.map((_, index) => {
      const heading = (from: number, to: number) => Math.atan2(at(coarseY, to) - at(coarseY, from), at(coarseX, to) - at(coarseX, from));
      let turn = heading(index, index + lookAhead) - heading(index - lookAhead, index);
      turn = Math.atan2(Math.sin(turn), Math.cos(turn));
      const radius = (lookAhead * step) / Math.max(Math.abs(turn), 1e-6);
      return Math.min(1, Math.max(0, (2 * bendRadius - radius) / bendRadius));
    }),
    12,
  );
  const [straightX, straightY] = straightened(bendX, bendY, bendiness, straightTolerance);
  const xs = bendX.map((x, index) => straightX[index] + (x - straightX[index]) * bendiness[index]);
  const ys = bendY.map((y, index) => straightY[index] + (y - straightY[index]) * bendiness[index]);
  const smoothWidths = blurLoop(sampleWidths, widthSigma);

  const every = Math.max(1, Math.round(spacing / step));
  const result: SmoothTrack = { points: [], widths: [] };
  for (let index = 0; index < count; index += every) {
    result.points.push([round(xs[index]), round(ys[index])]);
    result.widths.push(round(smoothWidths[index]));
  }
  return result;
}

/** Projects samples[from..to) onto their best-fit straight line, splitting the range where one line would stray more than `tolerance`. */
function projectOntoLines(xs: readonly number[], ys: readonly number[], from: number, to: number, tolerance: number, outX: number[], outY: number[]) {
  const count = to - from;
  let mx = 0;
  let my = 0;
  for (let i = from; i < to; i += 1) {
    mx += at(xs, i) / count;
    my += at(ys, i) / count;
  }
  let sxx = 0;
  let syy = 0;
  let sxy = 0;
  for (let i = from; i < to; i += 1) {
    const dx = at(xs, i) - mx;
    const dy = at(ys, i) - my;
    sxx += dx * dx;
    syy += dy * dy;
    sxy += dx * dy;
  }
  const angle = 0.5 * Math.atan2(2 * sxy, sxx - syy);
  const ux = Math.cos(angle);
  const uy = Math.sin(angle);
  let worst = 0;
  for (let i = from; i < to; i += 1) worst = Math.max(worst, Math.abs(-(at(xs, i) - mx) * uy + (at(ys, i) - my) * ux));
  if (worst > tolerance && count >= 16) {
    const middle = from + Math.floor(count / 2);
    projectOntoLines(xs, ys, from, middle, tolerance, outX, outY);
    projectOntoLines(xs, ys, middle, to, tolerance, outX, outY);
    return;
  }
  for (let i = from; i < to; i += 1) {
    const along = (at(xs, i) - mx) * ux + (at(ys, i) - my) * uy;
    outX[((i % xs.length) + xs.length) % xs.length] = mx + along * ux;
    outY[((i % xs.length) + xs.length) % xs.length] = my + along * uy;
  }
}

/** The samples with every long, nearly straight stretch (bendiness under one half) laid onto a ruler-straight line. */
function straightened(xs: readonly number[], ys: readonly number[], bendiness: readonly number[], tolerance: number, minimum = 24): [number[], number[]] {
  const count = xs.length;
  const outX = [...xs];
  const outY = [...ys];
  const straight = bendiness.map((b) => b < 0.5);
  // Begin at a bend so no straight run is cut by the array's edge.
  const start = straight.findIndex((flag) => !flag);
  if (start === -1) return [outX, outY];
  for (let offset = 0; offset < count; ) {
    const index = start + offset;
    if (!at(straight, index)) {
      offset += 1;
      continue;
    }
    let length = 0;
    while (offset + length < count && at(straight, index + length)) length += 1;
    if (length >= minimum) projectOntoLines(xs, ys, index, index + length, tolerance, outX, outY);
    offset += length;
  }
  // The lines meet with small steps where a run was split; a light blur turns each step into a gentle slope.
  return [blurLoop(outX, 6), blurLoop(outY, 6)];
}

/** Index of the waypoint closest to `target`. */
export function nearestIndex(points: readonly Point[], target: Point): number {
  let best = 0;
  points.forEach((p, index) => {
    if (Math.hypot(p[0] - target[0], p[1] - target[1]) < Math.hypot(points[best][0] - target[0], points[best][1] - target[1])) best = index;
  });
  return best;
}

/** The centre line as one closed cubic-Bézier path (used for anything that must travel along the track). */
export function circuitPath(points: readonly Point[]): string {
  const start = at(points, 0);
  let d = `M${start[0]} ${start[1]}`;
  for (let index = 0; index < points.length; index += 1) {
    const p0 = at(points, index - 1);
    const p1 = at(points, index);
    const p2 = at(points, index + 1);
    const p3 = at(points, index + 2);
    d += `C${round(p1[0] + (p2[0] - p0[0]) / 6)} ${round(p1[1] + (p2[1] - p0[1]) / 6)} ${round(p2[0] - (p3[0] - p1[0]) / 6)} ${round(p2[1] - (p3[1] - p1[1]) / 6)} ${p2[0]} ${p2[1]}`;
  }
  return `${d}Z`;
}

/** Direction of travel at a waypoint in degrees (0 = towards +x), for orienting things placed on the track. */
export function headingAt(points: readonly Point[], index: number): number {
  const before = at(points, index - 1);
  const after = at(points, index + 1);
  return (Math.atan2(after[1] - before[1], after[0] - before[0]) * 180) / Math.PI;
}

/** The road as a ribbon: centre line plus left and right edges offset by half the local width. */
export type Ribbon = {
  center: Point[];
  left: Point[];
  right: Point[];
  /** Unit vector from the centre towards the right edge. */
  normals: Point[];
  widths: number[];
};

export function buildRibbon(points: readonly Point[], widths: readonly number[], stepsPerSegment = 3): Ribbon {
  if (points.length !== widths.length) throw new Error("track: every waypoint needs a width");
  const ribbon: Ribbon = { center: [], left: [], right: [], normals: [], widths: [] };
  for (let index = 0; index < points.length; index += 1) {
    for (let step = 0; step < stepsPerSegment; step += 1) {
      const t = step / stepsPerSegment;
      const { x, y, dx, dy } = spline(points, index, t);
      const length = Math.hypot(dx, dy) || 1;
      const nx = -dy / length;
      const ny = dx / length;
      const width = at(widths, index) + (at(widths, index + 1) - at(widths, index)) * t;
      ribbon.center.push([round(x), round(y)]);
      ribbon.left.push([round(x - (nx * width) / 2), round(y - (ny * width) / 2)]);
      ribbon.right.push([round(x + (nx * width) / 2), round(y + (ny * width) / 2)]);
      ribbon.normals.push([nx, ny]);
      ribbon.widths.push(width);
    }
  }

  return ribbon;
}

/** A closed polygon as an SVG path. */
export function polygonPath(polygon: readonly Point[]): string {
  return `M${polygon.map(([x, y]) => `${x} ${y}`).join("L")}Z`;
}

/** Even-odd point-in-polygon test. */
export function insidePolygon(x: number, y: number, polygon: readonly Point[]): boolean {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i, i += 1) {
    const [xi, yi] = polygon[i];
    const [xj, yj] = polygon[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

/** A closed polyline as an SVG subpath. */
export function loopPath(polyline: readonly Point[]): string {
  return `M${polyline.map(([x, y]) => `${x} ${y}`).join("L")}Z`;
}

/**
 * Open subpaths along one side of the whole road, pushed `gap` units outside the asphalt edge. Samples for which `exclude` returns
 * true (e.g. open pavement, where tyres do not belong) split the path; the loop is closed when nothing is excluded.
 */
export function edgePath(ribbon: Ribbon, side: 1 | -1, gap: number, exclude: (x: number, y: number) => boolean = () => false): string {
  const count = ribbon.center.length;
  const samples: (Point | null)[] = ribbon.center.map((c, index) => {
    const n = ribbon.normals[index];
    const offset = ribbon.widths[index] / 2 + gap;
    const x = round(c[0] + n[0] * side * offset);
    const y = round(c[1] + n[1] * side * offset);
    return exclude(x, y) ? null : [x, y];
  });
  if (samples.every((sample) => sample !== null)) return loopPath(samples as Point[]);
  // Start just after an excluded sample so no run is split by the array's edge.
  const first = samples.findIndex((sample) => sample === null);
  let d = "";
  let open = false;
  for (let offset = 1; offset <= count; offset += 1) {
    const sample = at(samples, first + offset);
    if (sample === null) {
      open = false;
      continue;
    }
    d += `${open ? "L" : "M"}${sample[0]} ${sample[1]}`;
    open = true;
  }
  return d;
}
