import { site } from "@/content/site";

/** One line per schedule, so the two-line opening hours read the same on the home page, contact page and footer. */
export function WorkingHours() {
  return (
    <>
      {site.contact.openingHours.map(({ label, text }) => (
        <span key={label} className="block">
          {label}: {text}
        </span>
      ))}
    </>
  );
}
