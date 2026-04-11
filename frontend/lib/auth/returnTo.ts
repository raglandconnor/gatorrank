/** Build a same-origin return path for post-login redirects. */
export function buildReturnToFromWindow(): string {
  if (typeof window === 'undefined') return '/';
  const { pathname, search, hash } = window.location;
  return `${pathname}${search}${hash}`;
}

/**
 * Accept only in-app relative paths to prevent open redirects.
 * Falls back when input is missing or suspicious.
 */
export function resolveSafeReturnTo(
  raw: string | null | undefined,
  fallback = '/profile',
): string {
  if (!raw) return fallback;
  if (!raw.startsWith('/')) return fallback;
  if (raw.startsWith('//')) return fallback;
  return raw;
}
