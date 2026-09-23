import { site } from "@/content/site";

/** One line per schedule, so the two-line opening hours read the same on the home page, contact page and footer. */
export function WorkingHours() {
  return (
    <>
      {site.contact.hours.map((line) => (
        <span key={line} className="block">
          {line}
        </span>
      ))}
    </>
  );
}
