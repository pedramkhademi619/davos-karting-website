/**
 * Structured data for search engines. JSON-LD is data, not executed script, so the CSP does not need to allow it; "<" is
 * escaped so a value can never close the script element (the pattern from the Next.js JSON-LD guide).
 */
export function JsonLd({ data }: { data: Record<string, unknown> }) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, "\\u003c") }}
    />
  );
}
