const LINES = [
  { top: "14%", speed: "2.4s", delay: "0s" },
  { top: "27%", speed: "3.1s", delay: "0.9s" },
  { top: "41%", speed: "2.2s", delay: "1.6s" },
  { top: "58%", speed: "2.8s", delay: "0.4s" },
  { top: "72%", speed: "2.5s", delay: "2.1s" },
  { top: "86%", speed: "3.3s", delay: "1.2s" },
];

/** Decorative light streaks for the carbon cockpit panels (animated only without reduced motion). */
export function SpeedLines() {
  return (
    <div className="speed-lines" aria-hidden="true">
      {LINES.map((line) => (
        <span
          key={line.top}
          style={{ top: line.top, ["--speed" as string]: line.speed, ["--delay" as string]: line.delay }}
        />
      ))}
    </div>
  );
}
