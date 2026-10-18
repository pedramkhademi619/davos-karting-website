/** A small tyre-shaped spinner; `label` is read by screen readers. */
export function Spinner({ label = "در حال بارگذاری", className = "h-5 w-5" }: { label?: string; className?: string }) {
  return (
    <span role="status" className="inline-flex items-center">
      <svg viewBox="0 0 24 24" className={`animate-spin motion-reduce:animate-none ${className}`} aria-hidden="true">
        <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeOpacity="0.2" strokeWidth="4" />
        <path d="M12 3a9 9 0 0 1 9 9" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
      </svg>
      <span className="sr-only">{label}</span>
    </span>
  );
}
