/** `YYYY-MM-DD` for APIs that require date-only strings. */
export function toDateOnly(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export type MonthRange = { from: string; to: string };

/** Calendar month `[from, to]` relative to today (`published_from` / `published_to`). */
export function getMonthRange(offsetMonths = 0): MonthRange {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth() + offsetMonths, 1);
  const end = new Date(now.getFullYear(), now.getMonth() + offsetMonths + 1, 0);
  return { from: toDateOnly(start), to: toDateOnly(end) };
}
