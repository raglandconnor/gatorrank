import { apiUrl } from '@/lib/api/client';
import { buildHttpError, parseApiErrorMessage } from '@/lib/api/http';
import type { AuthRefreshBody, AuthTokenResponse } from '@/lib/api/types/auth';

/**
 * Raw refresh transport used by fetchWithAuth.
 * Kept separate from auth.ts to avoid circular imports with request.ts.
 */
export async function refreshAuthTokenRaw(
  body: AuthRefreshBody,
): Promise<AuthTokenResponse> {
  const res = await fetch(apiUrl('/api/v1/auth/refresh'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const message = await parseApiErrorMessage(res, 'Request failed');
    throw buildHttpError(message, res.status);
  }

  return res.json() as Promise<AuthTokenResponse>;
}
