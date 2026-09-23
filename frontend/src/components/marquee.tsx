/** Slow typographic ticker. Purely decorative, so it is hidden from assistive technology. */
export function Marquee({ words }: { words: readonly string[] }) {
  const row = (
    <ul className="flex shrink-0 items-center">
      {words.map((word, index) => (
        <li key={word} className="flex items-center">
          <span className={`px-8 text-5xl font-black md:px-12 md:text-7xl ${index % 2 === 0 ? "text-fg" : "text-line-strong"}`}>
            {word}
          </span>
          <span className="h-3 w-3 rotate-45 bg-accent" />
        </li>
      ))}
    </ul>
  );

  // dir="ltr" keeps the scroll maths simple; each Persian word still renders right-to-left inside its own span.
  return (
    <div className="marquee border-y border-line bg-surface py-7 md:py-9" dir="ltr" aria-hidden="true">
      <div className="marquee-track">
        {row}
        {row}
      </div>
    </div>
  );
}
