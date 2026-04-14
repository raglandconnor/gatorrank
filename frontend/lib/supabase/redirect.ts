const DEFAULT_POST_AUTH_REDIRECT = '/login';

/**
 * Restrict post-auth redirects to same-origin relative paths.
 *
 * Rejects:
 * - absolute URLs (https://example.com)
 * - protocol-relative URLs (//example.com)
 * - non-path values (e.g. "profile")
 */
export function getSafePostAuthRedirectPath(
  next: string | null | undefined,
  fallback = DEFAULT_POST_AUTH_REDIRECT,
): string {
  const candidate = (next ?? '').trim();
  if (!candidate) {
    return fallback;
  }
  if (!candidate.startsWith('/') || candidate.startsWith('//')) {
    return fallback;
  }
  return candidate;
}
