import { site } from "@/content/site";

const linkClass = "underline-offset-4 decoration-accent decoration-2 hover:underline";

/** Opens the track's location in a maps app: Google Maps, and the owner's pin on Neshan beside it. */
export function MapLink({ className = "" }: { className?: string }) {
  return (
    <span className={className}>
      <a href={site.contact.map.href} target="_blank" rel="noopener noreferrer" className={linkClass}>
        {site.contact.map.label}
      </a>
      <span aria-hidden="true"> · </span>
      <a href={site.contact.neshan.href} target="_blank" rel="noopener noreferrer" className={linkClass}>
        {site.contact.neshan.label}
      </a>
    </span>
  );
}
