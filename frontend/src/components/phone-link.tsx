import { site } from "@/content/site";

/** The booking phone number as a tap-to-call link; forced left-to-right so the digits are never reordered inside RTL text. */
export function PhoneLink({ className = "" }: { className?: string }) {
  return (
    <a
      href={site.contact.phone.href}
      dir="ltr"
      className={`inline-block underline-offset-4 decoration-accent decoration-2 hover:underline ${className}`}
    >
      {site.contact.phone.display}
    </a>
  );
}
