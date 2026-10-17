import { IntroSeen } from "@/components/intro-seen";

/**
 * The first-visit intro: a full-screen start gantry, five red lights, lights out, "داووس", and the page is revealed
 * (about three seconds, all CSS in globals.css). The site layout renders it only while the session cookie is missing,
 * so it plays once per visit; it never blocks clicks and is skipped entirely with reduced motion.
 */
export function Intro() {
  return (
    <div className="intro" aria-hidden="true">
      <div className="intro-panel" />
      <div className="intro-content">
        <div className="start-lights rounded-3xl bg-black/70 p-4 ring-1 ring-white/10">
          {[0, 1, 2, 3, 4].map((n) => (
            <span key={n} className="start-lamp" style={{ ["--n" as string]: n }} />
          ))}
        </div>
        <p className="intro-word glow-text">داووس</p>
      </div>
      <IntroSeen />
    </div>
  );
}
