/**
 * A configuration value the site cannot run without. There are no fallbacks in code: every value comes from the
 * repository's .env (docker-compose.yml passes it in), and a missing one stops the site with the variable's name.
 *
 * Pass `process.env.NAME` itself (not a computed key): Next.js inlines NEXT_PUBLIC_* values only when they are
 * written out literally.
 */
export function requiredEnv(name: string, value: string | undefined): string {
  const text = (value ?? "").trim();
  if (!text) throw new Error(`${name} is not set: add it to .env (see .env.example), then rebuild the frontend.`);
  return text;
}
