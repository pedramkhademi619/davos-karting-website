/** Fast typographic ticker on carbon, like trackside advertising boards. Purely decorative. */
export function Marquee({ words }: { words: readonly string[] }) {
  const row = (
    <ul className="flex shrink-0 items-center">
      {words.map((word, index) => (
        <li key={word} className="flex items-center">
          <span
            className={`px-8 text-5xl font-black md:px-12 md:text-7xl ${
              index % 2 === 0 ? "text-on-carbon" : "text-transparent [-webkit-text-stroke:1.5px_rgb(255_255_255/0.45)]"
            }`}
          >
            {word}
          </span>
          <span className="checker-bw h-5 w-5 rounded-sm" />
        </li>
      ))}
    </ul>
  );

  // dir="ltr" keeps the scroll maths simple; each Persian word still renders right-to-left inside its own span.
  return (
    <div className="marquee carbon-flat py-7 md:py-9" dir="ltr" aria-hidden="true">
      <div className="marquee-track">
        {row}
        {row}
      </div>
    </div>
  );
}
