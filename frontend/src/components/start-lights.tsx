/**
 * The Formula-style start gantry on one 6 s timeline: five red lamps light up one after another, all go out together,
 * then the green lamp and "GO".
 * Pure CSS (globals.css: lamp-1..lamp-5, lamp-go, go-word); with reduced motion the lamps stay dark and "GO" is simply shown.
 */
export function StartLights({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-4 ${className}`} aria-hidden="true">
      <div className="start-lights rounded-2xl bg-black/60 p-3 ring-1 ring-white/10">
        {[1, 2, 3, 4, 5].map((lamp) => (
          <span key={lamp} className={`start-lamp lamp-${lamp}`} />
        ))}
        <span className="start-lamp is-go" />
      </div>
      <span className="go-word race-number text-2xl font-black text-go">GO</span>
    </div>
  );
}
