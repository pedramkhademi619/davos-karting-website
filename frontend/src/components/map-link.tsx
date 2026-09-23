import { site } from "@/content/site";

/** Opens the track's location in the maps app; the site shows no street address because none has been confirmed. */
export function MapLink({ className = "" }: { className?: string }) {
  return (
    <a
      href={site.contact.map.href}
      target="_blank"
      rel="noopener noreferrer"
      className={`underline-offset-4 decoration-accent decoration-2 hover:underline ${className}`}
    >
      {site.contact.map.label}
    </a>
  );
}
