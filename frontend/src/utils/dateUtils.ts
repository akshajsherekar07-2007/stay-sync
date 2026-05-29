/**
 * Date formatting utilities.
 */

/**
 * Format an ISO date string to a human-readable format.
 */
export function formatDate(dateString: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(dateString));
}

/**
 * Format an ISO date string to relative time (e.g., "2 hours ago").
 */
export function formatRelativeTime(dateString: string): string {
  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  const diff = Date.now() - new Date(dateString).getTime();
  const seconds = Math.floor(diff / 1000);

  if (seconds < 60) return rtf.format(-seconds, "second");
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return rtf.format(-minutes, "minute");
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return rtf.format(-hours, "hour");
  const days = Math.floor(hours / 24);
  return rtf.format(-days, "day");
}
