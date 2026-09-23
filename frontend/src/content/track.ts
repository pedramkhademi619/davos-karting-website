import type { Point, Smoothing } from "@/lib/track-geometry";

/**
 * Top-down plan of the Davos karting track (29.76912 N, 52.49991 E), TRACED from a satellite image: the centre line and the lane
 * width at every waypoint were snapped onto the white edge lines of the asphalt, so the layout matches the photo to about 1-3 px
 * on an 821 px wide image. Coordinates are those image pixels (north up).
 *
 * What is NOT from the image: the satellite picture is old, so the kerbs are drawn as the yellow and red tyres that now line the
 * whole track (as seen in ground photos), the asphalt colour is the current dark surface, and the start/finish line position is a
 * guess on the straight beside the stands. Scenery (road, stands, terrace, planter, vegetation, fences) is a simplified redraw.
 * Nothing here is surveyed: do not use it for dimensions.
 */
export const TRACK_VIEWBOX = { x: 30, y: 0, width: 770, height: 583 } as const;

/** Circuit centre line, clockwise (north up the left straight, east along the top strip). Closed loop, ~16 px between waypoints. */
export const TRACK_POINTS: readonly Point[] = [
  [200.8, 453.5], [197.7, 437.8], [193.8, 422.3], [192.8, 406.3], [193.3, 390.3], [192.4, 374.3],
  [194.6, 358.6], [195.6, 342.8], [191, 327.5], [191.4, 311.5], [191.3, 295.6], [188.1, 279.9],
  [187.3, 263.9], [187.5, 247.9], [190.3, 232.2], [192.8, 216.4], [190, 200.7], [186, 185.3],
  [185.5, 169.3], [184.9, 153.3], [184.5, 137.3], [184.8, 121.3], [186.9, 105.5], [196.7, 93.3],
  [211.1, 86.3], [225.4, 79.1], [240.3, 73.6], [255.7, 77.3], [270.9, 82.5], [286, 87.8],
  [301.1, 93], [316.4, 98], [331.5, 103.3], [346.6, 108.5], [361.7, 113.8], [376.8, 119.1],
  [392, 124.2], [407.1, 129.4], [422.3, 134.6], [437.6, 139.4], [452.7, 144.7], [467.8, 150],
  [482.9, 155.1], [498.1, 160.3], [513.3, 165.3], [528.5, 170.4], [543.7, 175.5], [558.9, 180.5],
  [574.1, 185.5], [589.3, 190.6], [604.5, 195.3], [618.9, 202.5], [633.5, 208.8], [648, 215.6],
  [660.4, 225.7], [671.7, 237.1], [683.8, 247.5], [693.3, 260.1], [696.4, 275.8], [700.7, 291.2],
  [704.2, 306.8], [706.5, 322.7], [704.9, 338.5], [703.6, 354.4], [704.6, 370.3], [703.8, 386.3],
  [707.2, 401.9], [707.9, 417.8], [707, 433.8], [702.5, 449.1], [691.4, 460.4], [676.3, 465.3],
  [660.6, 462.9], [647.7, 453.6], [640.8, 439.4], [639.6, 423.4], [638.4, 407.5], [637.1, 391.5],
  [636, 375.5], [634.9, 359.6], [633.4, 343.6], [631.1, 327.8], [627.2, 312.3], [621.5, 297.3],
  [614.4, 283], [605.7, 269.6], [595.4, 257.3], [583.4, 246.7], [569.7, 238.4], [554.9, 232.3],
  [539.7, 227.5], [524.1, 223.7], [508.5, 220.2], [492.8, 216.9], [477.1, 213.9], [461.3, 211.1],
  [445.6, 208.3], [429.8, 205.4], [414, 202.7], [398.3, 200], [382.5, 197.1], [366.7, 194.3],
  [351, 191.5], [335.2, 189], [319.2, 187.4], [303.2, 187.9], [287.7, 191.5], [274.4, 200],
  [262.5, 210.7], [252.7, 222.9], [251.8, 238.8], [251.5, 254.8], [252.2, 270.8], [252.8, 286.8],
  [252.8, 302.8], [253.1, 318.8], [253.7, 334.8], [254.1, 350.8], [256.9, 366.6], [260.4, 382.2],
  [265.9, 397.2], [273.6, 411.3], [284.7, 422.6], [299.3, 429.1], [315.1, 430.9], [331, 429.4],
  [346.3, 424.7], [361, 418.4], [374.3, 409.5], [386.8, 399.5], [399.4, 389.6], [412.3, 380.1],
  [425.6, 371.2], [439.2, 362.7], [453.4, 355.5], [468.7, 350.7], [484.5, 348.7], [500.5, 349.9],
  [515.7, 354.8], [529.5, 362.8], [542, 372.8], [553.3, 384.1], [563.6, 396.4], [572.7, 409.5],
  [579.6, 424], [583.6, 439.5], [584.4, 455.4], [581.7, 471.1], [575, 485.6], [565.2, 498.3],
  [553.5, 509.2], [540.3, 518.2], [525.9, 525.1], [510.5, 529.6], [494.7, 532.2], [478.7, 532.6],
  [462.8, 531], [447, 528.4], [431.2, 525.6], [415.4, 523.1], [399.5, 521.3], [383.5, 520.5],
  [367.5, 520.8], [351.6, 522.5], [335.8, 525.2], [320.2, 528.8], [304.9, 533.5], [289.4, 537.1],
  [273.4, 537.7], [257.4, 537.2], [241.8, 534.4], [228.5, 525.6], [217.7, 513.9], [209.2, 500.3],
  [204.2, 485.2], [203.8, 469.2],
];

/** Lane width (edge line to edge line) at each waypoint, in the same units. */
export const TRACK_WIDTHS: readonly number[] = [
  31.3, 31.5, 31.5, 31.5, 31.5, 31.5, 31.5, 31.5, 31.5, 31.5, 31.5, 31.5, 31.5, 31.5, 31.5, 31.4,
  30.9, 30.4, 29.9, 29.4, 29.6, 30.1, 30.4, 30.8, 31.2, 32, 32.9, 33.9, 34.5, 34.6, 34.5, 34.4,
  34.3, 34.4, 34.5, 34.5, 34.6, 34.5, 34.3, 34.3, 34.4, 34.5, 34.7, 34.6, 34.5, 34.5, 34.3, 34.1,
  33.5, 32.9, 32.3, 31.5, 31.1, 30.8, 30.5, 30.5, 30.5, 30.4, 30.1, 29.5, 28.9, 29.1, 30, 30.8,
  31.4, 31.4, 31, 30.7, 30.8, 31, 31, 31, 31, 31, 30.9, 30.7, 30.4, 30.1, 29.7, 29.2,
  28.9, 28.6, 28.5, 28.6, 28.7, 28.7, 28.4, 28.2, 27.9, 27.7, 27.9, 28.1, 28.4, 28.8, 29, 29.2,
  29.4, 29.5, 29.5, 29.5, 29.5, 29.7, 30, 30.4, 30.6, 30.7, 30.6, 30.1, 29.2, 28.2, 27.4, 27,
  27.2, 27.9, 28.9, 30, 30.8, 31.2, 31.5, 31.5, 31.5, 31.9, 32.6, 33.4, 34.1, 33.8, 32.3, 30.5,
  29.1, 28.5, 28.5, 28.9, 29.7, 30.8, 31.9, 32.8, 33.6, 34.1, 34.4, 34.4, 34, 33.3, 32, 30.4,
  29, 28.2, 27.9, 28.3, 29, 29.5, 29.6, 29.3, 28.8, 28.5, 28.3, 28.5, 28.7, 28.9, 29, 29,
  29, 29, 28.9, 28.8, 28.8, 29.2, 29.7, 30.1, 30, 29.5, 28.9, 28.7, 29, 29.6, 30.4, 31,
];

/** How the traced line is smoothed before drawing (see smoothTrack). */
export const SMOOTHING: Smoothing = { bendSigma: 9, straightTolerance: 5, bendRadius: 120, widthSigma: 40, spacing: 10 };

/** Waypoint on the left straight beside the stands where the start/finish line is drawn. */
export const START_INDEX = 8;

/**
 * Wide paved plaza in the top-left corner. It runs down beside the stands only as far as the entrance (about y 190-234): below
 * that the aerial photo shows a strip of scrub between the racing lane and the pit side, drawn as green space (see VEGETATION).
 * Lane markings are redrawn on top of it.
 */
export const APRON: readonly Point[] = [
  [136, 25], [199, 40], [249, 56], [285, 72], [226, 99], [200, 123], [196, 234], [141, 234], [140, 190], [135, 110], [136, 60],
];
/** Island inside the apron (soil, outlined in white). */
export const PLANTER = { x: 142, y: 77, width: 29, height: 109, radius: 10 } as const;
/** Free edge of the apron along the top, up to where the strip's own edge line takes over. */
export const APRON_TOP_EDGE = "M136 25L199 40L250 56";

export const VEGETATION: readonly string[] = [
  // green strip between the racing lane and the pit side, below the entrance (its right side lies under the road)
  "M147 240L188 240L190 452L184 476L160 480L148 470Z",
  // infield crescent between the nested lane and the S-curve
  "M300 250L330 238L400 238L470 248L525 268L568 300L592 335L575 335L530 310L470 285L420 280L385 300L370 340L360 385L335 410L305 400L300 330Z",
  // patch inside the bulb
  "M385 470L400 440L430 410L470 398L500 405L525 430L530 460L505 480L455 485L410 480Z",
  // strip of dead scrub between the left straight and the S-curve
  "M208 215L238 215L240 300L236 400L246 470L226 475L210 430L206 320Z",
  // bottom-left thicket
  "M62 400L100 392L132 420L130 470L150 500L182 560L150 566L110 540L72 520L60 470Z",
];

export const LEFT_ROAD = "M30 0H49V583H30Z";
export const LEFT_ROAD_EDGE = "M51 95V545";
export const BUILDING = { cx: 86, cy: 52, rx: 46, ry: 41 } as const;
export const GRANDSTAND = "M68 150L123 108L124 332L70 292Z";
export const STEPS = { x: 123, y: 120, width: 23, height: 332 } as const;
export const TERRACE = { x: 95, y: 252, width: 22, height: 224 } as const;
export const PIT_BOXES: readonly (readonly [x: number, y: number])[] = [
  [66, 556], [80, 556], [94, 556], [108, 556], [122, 556], [136, 556],
];
export const FENCES: readonly { d: string; width: number; dash?: string; opacity: number }[] = [
  { d: "M781 232V540", width: 3.4, opacity: 0.85 },
  { d: "M765 240V530", width: 1.2, opacity: 0.5 },
  { d: "M105 553L790 545", width: 2, dash: "3 3", opacity: 0.6 },
];

export const TYRE_COLOURS = ["#FFC400", "#D62E14"] as const;
