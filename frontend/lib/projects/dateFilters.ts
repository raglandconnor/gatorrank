/** `YYYY-MM-DD` for APIs that require date-only strings. */
export function toDateOnly(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export type MonthRange = { from: string; to: string };
export type DateRange = { from: string; to: string };

const ALL_TIME_TOP_START = '1970-01-01';

/** Calendar month `[from, to]` relative to today (`published_from` / `published_to`). */
export function getMonthRange(offsetMonths = 0): MonthRange {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth() + offsetMonths, 1);
  const end = new Date(now.getFullYear(), now.getMonth() + offsetMonths + 1, 0);
  return { from: toDateOnly(start), to: toDateOnly(end) };
}

/** Explicit all-time range for `sort=top` to avoid backend 90-day default window. */
export function getAllTimeTopRange(): DateRange {
  return { from: ALL_TIME_TOP_START, to: toDateOnly(new Date()) };
}
