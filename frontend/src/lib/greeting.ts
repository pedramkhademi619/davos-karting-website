/** The hour in Tehran (0-23), whatever the visitor's own time zone is. */
function tehranHour(now: Date = new Date()): number {
  const hour = new Intl.DateTimeFormat("en-GB", { timeZone: "Asia/Tehran", hour: "numeric", hour12: false }).format(now);
  return Number(hour) % 24;
}

/** "صبح بخیر" / "ظهر بخیر" / "عصر بخیر" / "شب بخیر" for the time of day in Tehran. */
export function greeting(now: Date = new Date()): string {
  const hour = tehranHour(now);
  if (hour >= 5 && hour < 12) return "صبح بخیر";
  if (hour >= 12 && hour < 16) return "ظهر بخیر";
  if (hour >= 16 && hour < 20) return "عصر بخیر";
  return "شب بخیر";
}
