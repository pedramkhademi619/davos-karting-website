/** Decorative rev counter: the needle sweeps into the red and settles (CSS `needle` keyframes). Hidden from assistive tech. */
export function Tacho({ className = "" }: { className?: string }) {
  const ticks = Array.from({ length: 15 }, (_, i) => i);
  // The dial spans 240 degrees, from -120 (0 rpm) to +120 (14k rpm).
  const angle = (i: number) => -120 + (240 / 14) * i;
  return (
    <svg viewBox="0 0 200 200" className={className} aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="tacho-red" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#ff5a4d" />
          <stop offset="1" stopColor="#d90a00" />
        </linearGradient>
      </defs>
      <circle cx="100" cy="100" r="92" fill="#0f1115" stroke="rgb(255 255 255 / 0.08)" strokeWidth="2" />
      {/* Red zone from 11k to 14k rpm. */}
      <path d={arc(100, 100, 78, angle(11), angle(14))} fill="none" stroke="url(#tacho-red)" strokeWidth="9" strokeLinecap="round" />
      {ticks.map((i) => {
        const a = ((angle(i) - 90) * Math.PI) / 180;
        const inner = i % 2 === 0 ? 62 : 68;
        return (
          <line
            key={i}
            x1={100 + inner * Math.cos(a)}
            y1={100 + inner * Math.sin(a)}
            x2={100 + 74 * Math.cos(a)}
            y2={100 + 74 * Math.sin(a)}
            stroke={i >= 11 ? "#ff5a4d" : "rgb(255 255 255 / 0.7)"}
            strokeWidth={i % 2 === 0 ? 3 : 1.6}
            strokeLinecap="round"
          />
        );
      })}
      {ticks
        .filter((i) => i % 2 === 0)
        .map((i) => {
          const a = ((angle(i) - 90) * Math.PI) / 180;
          return (
            <text
              key={i}
              x={100 + 50 * Math.cos(a)}
              y={100 + 50 * Math.sin(a) + 4}
              textAnchor="middle"
              className="race-number"
              fontSize="10"
              fill="rgb(255 255 255 / 0.55)"
            >
              {i}
            </text>
          );
        })}
      <text x="100" y="140" textAnchor="middle" className="race-number" fontSize="9" fill="rgb(255 255 255 / 0.4)" letterSpacing="2">
        RPM x1000
      </text>
      <g className="needle" style={{ transformOrigin: "100px 100px", ["--needle" as string]: "72deg" }}>
        <path d="M100 100 L97 96 L100 28 L103 96 Z" fill="#ffc400" />
      </g>
      <circle cx="100" cy="100" r="9" fill="#1f222a" stroke="#ffc400" strokeWidth="2.5" />
    </svg>
  );
}

function arc(cx: number, cy: number, r: number, fromDeg: number, toDeg: number): string {
  const point = (deg: number) => {
    const a = ((deg - 90) * Math.PI) / 180;
    return `${(cx + r * Math.cos(a)).toFixed(2)} ${(cy + r * Math.sin(a)).toFixed(2)}`;
  };
  const large = toDeg - fromDeg > 180 ? 1 : 0;
  return `M ${point(fromDeg)} A ${r} ${r} 0 ${large} 1 ${point(toDeg)}`;
}
