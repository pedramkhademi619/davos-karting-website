/**
 * A go-kart seen from above, pointing along +x (so a path animation with rotate="auto" drives it nose first): four wheels,
 * the pod with its tapered nose and front wing, a rear bumper and the driver's helmet. About 26 units long; `colour` is the
 * body, so two karts on a track can be told apart. Put it inside a <g> that moves it.
 */
export function KartShape({ colour }: { colour: string }) {
  return (
    <g aria-hidden="true">
      {/* wheels: slicks, a little wider at the back */}
      <rect x="-11" y="-9" width="8" height="4.2" rx="1.4" fill="#0b0c0f" stroke="#3a3d45" strokeWidth="0.6" />
      <rect x="-11" y="4.8" width="8" height="4.2" rx="1.4" fill="#0b0c0f" stroke="#3a3d45" strokeWidth="0.6" />
      <rect x="5" y="-8.2" width="6.4" height="3.4" rx="1.2" fill="#0b0c0f" stroke="#3a3d45" strokeWidth="0.6" />
      <rect x="5" y="4.8" width="6.4" height="3.4" rx="1.2" fill="#0b0c0f" stroke="#3a3d45" strokeWidth="0.6" />
      {/* rear bumper and front wing */}
      <rect x="-13.5" y="-5.5" width="2.4" height="11" rx="1" fill="#16181d" stroke={colour} strokeWidth="0.8" />
      <rect x="11.2" y="-6.4" width="2.6" height="12.8" rx="1" fill={colour} />
      {/* the pod: wide behind the driver, tapering to the nose */}
      <path d="M-11 -5 L3 -5 L11.4 -2.2 L11.4 2.2 L3 5 L-11 5 Z" fill={colour} stroke="#0b0c0f" strokeWidth="1" strokeLinejoin="round" />
      {/* driver: helmet with a stripe, and the steering wheel in front of him */}
      <rect x="2.4" y="-3" width="1.4" height="6" rx="0.7" fill="#0b0c0f" />
      <circle cx="-2.4" cy="0" r="3.3" fill="#111317" stroke="#f4f4f5" strokeWidth="0.7" />
      <rect x="-4.6" y="-0.6" width="4.4" height="1.2" fill="#f4f4f5" opacity="0.85" />
    </g>
  );
}
